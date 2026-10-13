// worldforge/native/rmcobject_decoder.cpp -- see rmcobject_decoder.hpp and RMCOBJECT_MAPPING.md.
//
// Sneeze 0008d08 / Map 0e6d26a / RMAP 0fd7efb. Include order follows Sneeze's precompiled header
// (src/sneeze/Pch.h:79-85): the <Sneeze.h> umbrella first, then <RMAP/RMAP.h>.

#include "rmcobject_decoder.hpp"

#include <cmath>
#include <cstring>
#include <functional>
#include <unordered_map>

#include <Sneeze.h>          // SNEEZE::OBJECTIX_IDENTITY / OBJECTIX_ERROR (include/Scene.h:40-46)
#include <RMAP/RMAP.h>       // OBJECTIX_COMPOSE (RMAP/include/RMAP/Mem.h:12)

#ifdef WORLDFORGE_LINK_SNEEZE
#include "context/scene/RmcObject.h"   // SNEEZE::MOCelestial_FromJson, SNEEZE::RESOURCE_SUPPLEMENT
#endif

// ---------------------------------------------------------------------------------------------------
// Layout facts the mapping document relies on. If any of these change upstream, the syntax-only
// compile in check_decoder.sh fails and RMCOBJECT_MAPPING.md has to be re-verified.
// ---------------------------------------------------------------------------------------------------

namespace
{
   using POD = RMAP::MAP::MAP_OBJECT_POD;

   static_assert (sizeof (POD)                                    == 504, "MAP_OBJECT_POD size (Map_Object.h:124-134)");
   static_assert (offsetof (POD, Name)                            ==   0, "Name offset");
   static_assert (offsetof (POD, Type)                            ==  96, "Type offset");
   static_assert (offsetof (POD, Owner)                           == 104, "Owner offset");
   static_assert (offsetof (POD, Resource)                        == 112, "Resource offset");
   static_assert (offsetof (POD, Transform)                       == 312, "Transform offset");
   static_assert (offsetof (POD, Orbit)                           == 392, "Orbit offset");
   static_assert (offsetof (POD, Bound)                           == 424, "Bound offset");
   static_assert (offsetof (POD, Properties)                      == 472, "Properties offset");
   static_assert (WORLDFORGE::NATIVE::kNAME_UNITS_FIELD           ==  48, "wsName[48] (Map_Object.h:28)");
   static_assert (WORLDFORGE::NATIVE::kREFERENCE_BYTES_MAX        == 127, "sReference[128] (Map_Object.h:48)");
   static_assert (WORLDFORGE::NATIVE::kRESNAME_BYTES_MAX          ==  63, "sName[64] (Map_Object.h:47)");
   static_assert (sizeof (RMAP::MAP::MAP_OBJECT_TRANSFORM::d4Rotation) == 4 * sizeof (double), "d4Rotation[4] (Map_Object.h:54)");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_ROOT                ==  70, "Map_Object.h:18");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_CELESTIAL           ==  71, "Map_Object.h:19");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_TERRESTRIAL         ==  72, "Map_Object.h:20");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_PHYSICAL            ==  73, "Map_Object.h:21");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_PANEL               ==  74, "Map_Object.h:22");
   static_assert (RMAP::MAP::MAP_OBJECT_CLASS_LIGHT               ==  75, "Map_Object.h:23");
   static_assert (SNEEZE::OBJECTIX_IDENTITY                       == 0x0000FFFFFFFFFFFFull, "Scene.h:45");
   static_assert (SNEEZE::OBJECTIX_ERROR                          == 0x0000FFFFFFFFFFFEull, "Scene.h:43");

   // Plan nativeClass spellings -> MAP_OBJECT_CLASS. The plan uses the derived-type names from the
   // Scene.md:364-371 table; the enum spellings from Map_Object.h:16-24 are accepted as well.
   struct CLASS_NAME
   {
      const char* pszPlan;
      uint16_t    wClass;
      char        cJsonLetter;   // RmcObject.cpp:81-86 "<letter>-<index>" id; 0 = no letter (PANEL)
   };

   const CLASS_NAME g_aClass[] =
   {
      { "MAP_OBJECT_ROOT",                   RMAP::MAP::MAP_OBJECT_CLASS_ROOT,        'R' },
      { "MAP_OBJECT_CELESTIAL",              RMAP::MAP::MAP_OBJECT_CLASS_CELESTIAL,   'C' },
      { "MAP_OBJECT_TERRESTRIAL",            RMAP::MAP::MAP_OBJECT_CLASS_TERRESTRIAL, 'T' },
      { "MAP_OBJECT_PHYSICAL",               RMAP::MAP::MAP_OBJECT_CLASS_PHYSICAL,    'P' },
      { "MAP_OBJECT_PANEL",                  RMAP::MAP::MAP_OBJECT_CLASS_PANEL,        0  },
      { "MAP_OBJECT_LIGHT",                  RMAP::MAP::MAP_OBJECT_CLASS_LIGHT,       'L' },
      { "MAP_OBJECT_CLASS_ROOT",             RMAP::MAP::MAP_OBJECT_CLASS_ROOT,        'R' },
      { "MAP_OBJECT_CLASS_CELESTIAL",        RMAP::MAP::MAP_OBJECT_CLASS_CELESTIAL,   'C' },
      { "MAP_OBJECT_CLASS_TERRESTRIAL",      RMAP::MAP::MAP_OBJECT_CLASS_TERRESTRIAL, 'T' },
      { "MAP_OBJECT_CLASS_PHYSICAL",         RMAP::MAP::MAP_OBJECT_CLASS_PHYSICAL,    'P' },
      { "MAP_OBJECT_CLASS_PANEL",            RMAP::MAP::MAP_OBJECT_CLASS_PANEL,        0  },
      { "MAP_OBJECT_CLASS_LIGHT",            RMAP::MAP::MAP_OBJECT_CLASS_LIGHT,       'L' },
   };

   const CLASS_NAME* Class_Find (const std::string& sName)
   {
      for (const CLASS_NAME& c : g_aClass)
         if (sName == c.pszPlan)
            return &c;
      return nullptr;
   }

   const CLASS_NAME* Class_FromValue (uint16_t wClass)
   {
      for (const CLASS_NAME& c : g_aClass)
         if (c.wClass == wClass)
            return &c;
      return nullptr;
   }

   // Avoid emitting -0.0 when an axis flip hits a zero.
   double Neg (double d) { return (d == 0.0) ? 0.0 : -d; }

   bool Finite_Array (const nlohmann::json& a, size_t n, double* pd)
   {
      if (!a.is_array () || a.size () != n)
         return false;
      for (size_t i = 0; i < n; i++)
      {
         if (!a[i].is_number ())
            return false;
         pd[i] = a[i].get<double> ();
         if (!std::isfinite (pd[i]))
            return false;
      }
      return true;
   }

   // UTF-8 -> UTF-16, BMP only (NODE::Name reads the field back as BMP UTF-16: Node.cpp:713-735).
   // Invalid sequences, surrogates and non-BMP code points become U+FFFD.
   std::u16string Utf8_To_Bmp (const std::string& s, size_t& nReplaced)
   {
      static const uint32_t s_adwMin[5] = { 0, 0, 0x80, 0x800, 0x10000 };

      std::u16string w;
      size_t         i = 0;
      const size_t   n = s.size ();

      while (i < n)
      {
         const unsigned char c = static_cast<unsigned char> (s[i]);
         uint32_t cp;
         size_t   nLen;

         if      (c < 0x80)           { cp = c;        nLen = 1; }
         else if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; nLen = 2; }
         else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; nLen = 3; }
         else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; nLen = 4; }
         else                         { w.push_back (u'�'); nReplaced++; i++; continue; }

         bool bOk = (i + nLen <= n);
         for (size_t k = 1; bOk && k < nLen; k++)
         {
            const unsigned char cc = static_cast<unsigned char> (s[i + k]);
            if ((cc & 0xC0) != 0x80)
               bOk = false;
            else
               cp = (cp << 6) | (cc & 0x3F);
         }

         if (!bOk)
         {
            w.push_back (u'�'); nReplaced++; i++; continue;
         }

         if (cp < s_adwMin[nLen] || (cp >= 0xD800 && cp <= 0xDFFF) || cp > 0xFFFF)
         {
            w.push_back (u'�'); nReplaced++;
         }
         else w.push_back (static_cast<char16_t> (cp));

         i += nLen;
      }

      return w;
   }

   std::string Str (const nlohmann::json& j, const char* pszKey)
   {
      return (j.is_object () && j.contains (pszKey) && j[pszKey].is_string ()) ? j[pszKey].get<std::string> () : std::string ();
   }
}

namespace WORLDFORGE
{
   namespace NATIVE
   {
      RMCOBJECT_DECODED RmcObjectDecoder (const nlohmann::json& spec)
      {
         return RmcObjectDecoder (spec, RMCOBJECT_DECODE_OPTIONS ());
      }

      RMCOBJECT_DECODED RmcObjectDecoder (const nlohmann::json& spec, const RMCOBJECT_DECODE_OPTIONS& Options)
      {
         RMCOBJECT_DECODED d;

         // Start from the same defaults SNEEZE::MOCelestial_FromJson uses: a zeroed POD, identity
         // quaternion and unit scale (RmcObject.cpp:105-115, RmcObject.h:25-28).
         std::memset (&d.Pod, 0, sizeof (d.Pod));
         d.Pod.Transform.d4Rotation[3] = 1.0;
         d.Pod.Transform.d3Scale[0]    = 1.0;
         d.Pod.Transform.d3Scale[1]    = 1.0;
         d.Pod.Transform.d3Scale[2]    = 1.0;

         if (!spec.is_object ())
         {
            d.asErrors.push_back ("spec is not an object");
            return d;
         }

         // ---- cardId / parentCardId / extras: no native slot ----------------------------------------
         d.sCardId = Str (spec, "cardId");
         if (d.sCardId.empty ())
            d.asErrors.push_back ("cardId missing");

         if (spec.contains ("parentCardId") && spec["parentCardId"].is_string ())
            d.sParentCardId = spec["parentCardId"].get<std::string> ();
         else if (spec.contains ("parentCardId") && spec["parentCardId"].is_null ())
            d.bRoot = true;
         else
            d.asErrors.push_back ("parentCardId must be a string or null");

         if (spec.contains ("extras"))
            d.jExtras = spec["extras"];

         // ---- nativeClass -> wClass (Map_Object.h:16-24) ---------------------------------------------
         const std::string  sClass = Str (spec, "nativeClass");
         const CLASS_NAME*  pClass = Class_Find (sClass);

         if (pClass)
         {
            d.wClass = pClass->wClass;
            if (d.wClass == RMAP::MAP::MAP_OBJECT_CLASS_ROOT)
               d.asWarnings.push_back ("class ROOT is what the scene's own root fabric uses (Scene.md:366)");
            if (d.wClass == RMAP::MAP::MAP_OBJECT_CLASS_LIGHT)
               d.asWarnings.push_back ("class LIGHT reads Properties.Light, which the plan does not carry");
         }
         else d.asErrors.push_back ("unknown nativeClass '" + sClass + "' (Map_Object.h:16-24)");

         // The container assigns the next free index (Container.cpp:319-325). Explicit indices are
         // de-duplicated per container (Container.cpp:326-333), so the plan does not pick them.
         d.twObjectIx = SNEEZE::OBJECTIX_IDENTITY;

         // ---- displayName -> Name.wsName[48], UTF-16 (Map_Object.h:26-29) --------------------------
         if (spec.contains ("displayName") && spec["displayName"].is_string ())
         {
            size_t         nReplaced = 0;
            std::u16string w         = Utf8_To_Bmp (spec["displayName"].get<std::string> (), nReplaced);
            size_t         nUnits    = w.size ();

            if (nUnits > kNAME_UNITS_MAX)
            {
               d.asWarnings.push_back ("name clamped from " + std::to_string (nUnits) + " to " + std::to_string (kNAME_UNITS_MAX) + " UTF-16 units (wsName[48] keeps a NUL)");
               nUnits = kNAME_UNITS_MAX;
            }
            if (nReplaced)
               d.asWarnings.push_back ("name: " + std::to_string (nReplaced) + " code point(s) not representable in BMP UTF-16 became U+FFFD");

            for (size_t i = 0; i < nUnits; i++)
            {
               if (w[i] == 0)
               {
                  d.asErrors.push_back ("name contains U+0000; NODE::Name stops there (Node.cpp:717)");
                  break;
               }
               d.Pod.Name.wsName[i] = static_cast<uint16_t> (w[i]);
            }
            // wsName[nUnits..47] remain 0 from the memset: always NUL-terminated.
         }
         else d.asErrors.push_back ("displayName missing");

         // ---- Type / Owner: not in the plan; zero ---------------------------------------------------
         // bSubtype must not be 255: that makes the node an MSF attachment point and its sReference is
         // spawned as a fabric instead of being fetched as a model (Node.cpp:155-167).
         d.Pod.Type.bType    = 0;
         d.Pod.Type.bSubtype = 0;
         d.Pod.Type.bFiction = 0;
         d.Pod.Owner.twOwner = 0;

         // ---- resource.sReference -> Resource.sReference[128] (Map_Object.h:44-49) ----------------
         if (spec.contains ("resource") && spec["resource"].is_object ())
         {
            const nlohmann::json& r    = spec["resource"];
            const std::string     sRef = Str (r, "sReference");

            if (sRef.empty ())
               d.asErrors.push_back ("resource present but sReference empty: no fetch happens (Node.cpp:155)");
            else if (sRef.size () > kREFERENCE_BYTES_MAX)
               d.asErrors.push_back ("sReference is " + std::to_string (sRef.size ()) + " bytes; the field holds 127 plus a NUL (Map_Object.h:48). A truncated URL would not resolve, so this is refused.");
            else
            {
               if (sRef.compare (0, 7, "action:") == 0)
                  d.asErrors.push_back ("sReference starting with 'action:' is never fetched (Node.cpp:207)");
               std::memcpy (d.Pod.Resource.sReference, sRef.data (), sRef.size ());
            }

            const std::string sName = Str (r, "sName");
            if (sName.size () > kRESNAME_BYTES_MAX)
               d.asErrors.push_back ("resource.sName exceeds 63 bytes (Map_Object.h:47)");
            else if (!sName.empty ())
               std::memcpy (d.Pod.Resource.sName, sName.data (), sName.size ());

            d.Pod.Resource.qwResource = 0;
         }
         else if (spec.contains ("resource") && !spec["resource"].is_null ())
            d.asErrors.push_back ("resource must be an object or null");

         // ---- transform -> Transform {d3Position, d4Rotation(x,y,z,w), d3Scale} (Map_Object.h:51-56) --
         const nlohmann::json& tr = spec.contains ("transform") ? spec["transform"] : nlohmann::json ();
         double adT[3] = { 0.0, 0.0, 0.0 };
         double adQ[4] = { 0.0, 0.0, 0.0, 1.0 };
         double adS[3] = { 1.0, 1.0, 1.0 };

         if (!tr.is_object ())
            d.asErrors.push_back ("transform missing");
         else
         {
            if (!Finite_Array (tr.contains ("translation") ? tr["translation"] : nlohmann::json (), 3, adT))
               d.asErrors.push_back ("transform.translation must be 3 finite numbers");

            if (!Finite_Array (tr.contains ("rotation") ? tr["rotation"] : nlohmann::json (), 4, adQ))
               d.asErrors.push_back ("transform.rotation must be 4 finite numbers [x,y,z,w]");
            else
            {
               // Compositor.cpp:231-249 builds the matrix straight from the quaternion with no
               // normalisation, so a non-unit quaternion would shear and scale the node.
               const double dNorm = std::sqrt (adQ[0] * adQ[0] + adQ[1] * adQ[1] + adQ[2] * adQ[2] + adQ[3] * adQ[3]);
               if (!(dNorm > 0.0))
                  d.asErrors.push_back ("transform.rotation has zero length");
               else if (std::fabs (dNorm - 1.0) > kQUAT_TOLERANCE)
               {
                  d.asWarnings.push_back ("rotation renormalised (|q| = " + std::to_string (dNorm) + ")");
                  for (double& q : adQ)
                     q /= dNorm;
               }
            }

            if (!Finite_Array (tr.contains ("scale") ? tr["scale"] : nlohmann::json (), 3, adS))
               d.asErrors.push_back ("transform.scale must be 3 finite numbers");
            else if (adS[0] == 0.0 || adS[1] == 0.0 || adS[2] == 0.0)
               d.asErrors.push_back ("transform.scale has a zero axis; it would collapse every descendant (RmcObject.h:25-28)");
         }

         if (Options.eUp == UP_AXIS::Y)
         {
            // C = Rx(+90deg). Position: C t. Rotation: C R C^-1, which keeps w and rotates the vector
            // part. Scale: C S C^-1 = diag(sx, sz, sy). This is the same map GltfMesh.cpp:1827-1830
            // applies to every imported model, so a resource (glTF, Y-up) and its node stay aligned.
            d.Pod.Transform.d3Position[0] = adT[0];
            d.Pod.Transform.d3Position[1] = Neg (adT[2]);
            d.Pod.Transform.d3Position[2] = adT[1];
            d.Pod.Transform.d4Rotation[0] = adQ[0];
            d.Pod.Transform.d4Rotation[1] = Neg (adQ[2]);
            d.Pod.Transform.d4Rotation[2] = adQ[1];
            d.Pod.Transform.d4Rotation[3] = adQ[3];
            d.Pod.Transform.d3Scale[0]    = adS[0];
            d.Pod.Transform.d3Scale[1]    = adS[2];
            d.Pod.Transform.d3Scale[2]    = adS[1];
         }
         else
         {
            for (int i = 0; i < 3; i++) d.Pod.Transform.d3Position[i] = adT[i];
            for (int i = 0; i < 4; i++) d.Pod.Transform.d4Rotation[i] = adQ[i];
            for (int i = 0; i < 3; i++) d.Pod.Transform.d3Scale[i]    = adS[i];
         }

         // ---- Bound.d3Max: full extent in metres (Compositor.cpp:647-653, 734-742) -------------------
         // The mount plan carries no volume. cards.json does (volum.halfExtents), so a spec that adds
         // "volum" is honoured here. Without it Bound stays zero.
         if (spec.contains ("volum") && spec["volum"].is_object ())
         {
            double adH[3];
            if (Finite_Array (spec["volum"].contains ("halfExtents") ? spec["volum"]["halfExtents"] : nlohmann::json (), 3, adH))
            {
               const bool bY = (Options.eUp == UP_AXIS::Y);
               d.Pod.Bound.d3Max[0] = 2.0 * adH[0];
               d.Pod.Bound.d3Max[1] = 2.0 * (bY ? adH[2] : adH[1]);
               d.Pod.Bound.d3Max[2] = 2.0 * (bY ? adH[1] : adH[2]);
            }
            else d.asErrors.push_back ("volum.halfExtents must be 3 finite numbers");
         }
         else d.asWarnings.push_back ("no volum in spec: Bound.d3Max left zero");

         // Orbit (celestial only, Map_Object.h:66-73) and Properties (Map_Object.h:114-122) stay zero.
         return d;
      }

      std::vector<RMCOBJECT_DECODED> MountPlanDecode (const nlohmann::json& plan, std::vector<std::string>& asErrors)
      {
         std::vector<RMCOBJECT_DECODED> aDecoded;

         if (!plan.is_object () || !plan.contains ("nodes") || !plan["nodes"].is_array ())
         {
            asErrors.push_back ("plan has no nodes array");
            return aDecoded;
         }

         RMCOBJECT_DECODE_OPTIONS Options;
         const std::string sUp = (plan.contains ("coordinateFrame") && plan["coordinateFrame"].is_object ()) ? Str (plan["coordinateFrame"], "up") : std::string ();

         if      (sUp == "Y") Options.eUp = UP_AXIS::Y;
         else if (sUp == "Z") Options.eUp = UP_AXIS::Z;
         else asErrors.push_back ("coordinateFrame.up must be \"Y\" or \"Z\" (got '" + sUp + "')");

         const std::string sRoot = Str (plan, "rootCardId");
         std::unordered_map<std::string, size_t> mpSeen;

         for (const nlohmann::json& jNode : plan["nodes"])
         {
            RMCOBJECT_DECODED d   = RmcObjectDecoder (jNode, Options);
            const size_t      nIx = aDecoded.size ();

            if (!d.sCardId.empty ())
            {
               if (mpSeen.count (d.sCardId))
                  asErrors.push_back ("duplicate cardId " + d.sCardId);
               else
                  mpSeen[d.sCardId] = nIx;
            }

            if (d.bRoot)
            {
               if (nIx != 0)
                  asErrors.push_back ("root " + d.sCardId + " is not the first node");
               if (!sRoot.empty () && d.sCardId != sRoot)
                  asErrors.push_back ("root " + d.sCardId + " is not rootCardId " + sRoot);
            }
            else if (!d.sParentCardId.empty () && !mpSeen.count (d.sParentCardId))
            {
               // Node_Open needs the parent's handle, so the parent must already exist (Container.cpp:305-308).
               asErrors.push_back ("parent " + d.sParentCardId + " of " + d.sCardId + " is not earlier in the plan");
            }

            aDecoded.push_back (std::move (d));
         }

         if (aDecoded.empty () || !aDecoded.front ().bRoot)
            asErrors.push_back ("first node is not a root (parentCardId null)");

         return aDecoded;
      }

      nlohmann::json RmcObjectNodeJson (const RMCOBJECT_DECODED& Decoded, std::vector<std::string>& asWarnings)
      {
         nlohmann::json j = nlohmann::json::object ();

         // Head.Self (RmcObject.cpp:147-168). The "<letter>-?" form (RmcObject.cpp:67-90) is preferred:
         // the composed integer form is above 2^53 for every class, so a JSON file produced by JavaScript
         // would lose it. PANEL has no letter, so it uses the integer form, as Scene.cpp:478 does.
         const CLASS_NAME* pClass = Class_FromValue (Decoded.wClass);
         if (pClass && pClass->cJsonLetter)
            j["Head"]["Self"] = std::string (1, pClass->cJsonLetter) + "-?";
         else
         {
            j["Head"]["Self"] = static_cast<uint64_t> (OBJECTIX_COMPOSE (Decoded.wClass, SNEEZE::OBJECTIX_IDENTITY));
            asWarnings.push_back ("Head.Self written as a 64-bit integer; JavaScript JSON tooling would round it");
         }

         // Name (RmcObject.cpp:170-173 -> 136-145). That path copies bytes one-per-unit and passes
         // sizeof(wsName) = 96 as the unit limit, so it is only safe for ASCII names of at most 47 bytes.
         std::string sName;
         size_t      nFolded = 0;
         for (size_t i = 0; i < kNAME_UNITS_FIELD && Decoded.Pod.Name.wsName[i] != 0; i++)
         {
            const uint16_t u = Decoded.Pod.Name.wsName[i];
            if (u < 0x80)
               sName.push_back (static_cast<char> (u));
            else
            {
               sName.push_back ('?');
               nFolded++;
            }
         }
         if (sName.size () > kNAME_UNITS_MAX)
            sName.resize (kNAME_UNITS_MAX);
         if (nFolded)
            asWarnings.push_back ("json route: " + std::to_string (nFolded) + " non-ASCII name unit(s) written as '?' (RmcObject.cpp:136-145 copies bytes, not code points)");
         j["Name"] = sName;

         // Type (RmcObject.cpp:175-181). Written explicitly so a later name-overflow bug upstream cannot
         // leave bSubtype = 255 behind (see RMCOBJECT_MAPPING.md, upstream defects).
         j["Type"] = { { "bType",    Decoded.Pod.Type.bType },
                       { "bSubtype", Decoded.Pod.Type.bSubtype },
                       { "bFiction", Decoded.Pod.Type.bFiction } };

         if (Decoded.Pod.Owner.twOwner)
            j["Owner"] = Decoded.Pod.Owner.twOwner;

         // Resource (RmcObject.cpp:185-226)
         if (Decoded.Pod.Resource.sReference[0] != '\0')
         {
            nlohmann::json r = nlohmann::json::object ();
            r["sReference"] = std::string (Decoded.Pod.Resource.sReference, strnlen (Decoded.Pod.Resource.sReference, sizeof (Decoded.Pod.Resource.sReference)));
            if (Decoded.Pod.Resource.sName[0] != '\0')
               r["sName"] = std::string (Decoded.Pod.Resource.sName, strnlen (Decoded.Pod.Resource.sName, sizeof (Decoded.Pod.Resource.sName)));
            if (Decoded.Pod.Resource.qwResource)
               r["qwResource"] = Decoded.Pod.Resource.qwResource;
            j["Resource"] = r;
         }

         // Transform (RmcObject.cpp:228-234). The values are already in Sneeze's Z-up frame.
         const RMAP::MAP::MAP_OBJECT_TRANSFORM& t = Decoded.Pod.Transform;
         j["Transform"]["Position"] = { t.d3Position[0], t.d3Position[1], t.d3Position[2] };
         j["Transform"]["Rotation"] = { t.d4Rotation[0], t.d4Rotation[1], t.d4Rotation[2], t.d4Rotation[3] };
         j["Transform"]["Scale"]    = { t.d3Scale[0],    t.d3Scale[1],    t.d3Scale[2] };

         // Bound (RmcObject.cpp:245-246)
         const double* pdMax = Decoded.Pod.Bound.d3Max;
         if (pdMax[0] != 0.0 || pdMax[1] != 0.0 || pdMax[2] != 0.0)
            j["Bound"]["Max"] = { pdMax[0], pdMax[1], pdMax[2] };

         // Orbit / Properties omitted: zero for these classes, and any "Properties" key would make the
         // decoder write fColor (RmcObject.cpp:248-300).
         return j;
      }

      nlohmann::json MountPlanToBranch (const nlohmann::json& plan, std::vector<std::string>& asErrors, std::vector<std::string>& asWarnings)
      {
         std::vector<RMCOBJECT_DECODED> aDecoded = MountPlanDecode (plan, asErrors);

         for (const RMCOBJECT_DECODED& d : aDecoded)
            for (const std::string& s : d.asErrors)
               asErrors.push_back (d.sCardId + ": " + s);

         if (!asErrors.empty () || aDecoded.empty ())
            return nlohmann::json ();

         std::unordered_map<std::string, size_t> mpIx;
         std::vector<std::vector<size_t>>        aaChildren (aDecoded.size ());

         for (size_t i = 0; i < aDecoded.size (); i++)
         {
            mpIx[aDecoded[i].sCardId] = i;
            if (!aDecoded[i].bRoot)
               aaChildren[mpIx.at (aDecoded[i].sParentCardId)].push_back (i);
         }

         std::vector<std::string> asNodeWarnings;
         std::function<nlohmann::json (size_t)> Build = [&] (size_t nIx) -> nlohmann::json
         {
            nlohmann::json j = RmcObjectNodeJson (aDecoded[nIx], asNodeWarnings);
            if (!aaChildren[nIx].empty ())
            {
               nlohmann::json a = nlohmann::json::array ();
               for (size_t c : aaChildren[nIx])
                  a.push_back (Build (c));
               j["aChildren"] = std::move (a);   // Container.cpp:54
            }
            return j;
         };

         nlohmann::json jBranch = Build (0);
         asWarnings.insert (asWarnings.end (), asNodeWarnings.begin (), asNodeWarnings.end ());
         return jBranch;
      }

#ifdef WORLDFORGE_LINK_SNEEZE
      RMAP::MAP::MAP_OBJECT* RmcObjectCreate (const RMCOBJECT_DECODED& Decoded)
      {
         return RMAP::MAP::MAP_OBJECT::Create (Decoded.wClass, Decoded.twObjectIx, Decoded.Pod);
      }

      bool MountPlanApply (SNEEZE::CONTAINER* pContainer, const MOUNT_TARGET& Target, const std::vector<RMCOBJECT_DECODED>& aDecoded, std::vector<uint64_t>& aqwHandle, std::vector<std::string>& asErrors)
      {
         std::unordered_map<std::string, uint64_t> mpHandle;

         aqwHandle.clear ();

         if (pContainer == nullptr)
         {
            asErrors.push_back ("no container");
            return false;
         }

         for (const RMCOBJECT_DECODED& d : aDecoded)
         {
            if (!d.Ok ())
            {
               asErrors.push_back (d.sCardId + ": not decodable");
               return false;
            }

            RMAP::MAP::MAP_OBJECT* pMap_Object = RmcObjectCreate (d);
            if (pMap_Object == nullptr)
            {
               asErrors.push_back (d.sCardId + ": MAP_OBJECT::Create returned null");
               return false;
            }

            uint64_t qwComposed = SNEEZE::OBJECTIX_ERROR;

            if (d.bRoot)
               qwComposed = Target.bFabricRoot ? pContainer->Node_Root (Target.twFabricIx, pMap_Object)
                                               : pContainer->Node_Open (Target.qwComposed_Parent, pMap_Object);
            else
            {
               auto it = mpHandle.find (d.sParentCardId);
               if (it != mpHandle.end ())
                  qwComposed = pContainer->Node_Open (it->second, pMap_Object);   // composed handle (Container.cpp:342)
            }

            if (qwComposed == SNEEZE::OBJECTIX_ERROR)
            {
               delete pMap_Object;   // as Branch_Add does (Container.cpp:449, 484)
               asErrors.push_back (d.sCardId + ": Node_Root/Node_Open returned OBJECTIX_ERROR");
               return false;
            }

            if (pContainer->Node_Find (qwComposed) == nullptr)
            {
               asErrors.push_back (d.sCardId + ": handle does not resolve via CONTAINER::Node_Find");
               return false;
            }

            mpHandle[d.sCardId] = qwComposed;
            aqwHandle.push_back (qwComposed);
         }

         return true;
      }

      bool RmcObjectCrossCheck (const RMCOBJECT_DECODED& Decoded, std::string& sDiff)
      {
         std::vector<std::string>                 asWarnings;
         const nlohmann::json                     j = RmcObjectNodeJson (Decoded, asWarnings);
         uint16_t                                 wClass     = 0;
         uint64_t                                 twObjectIx = 0;
         RMAP::MAP::MAP_OBJECT_POD                Pod;
         std::vector<SNEEZE::RESOURCE_SUPPLEMENT> aSupplementary;

         SNEEZE::MOCelestial_FromJson (j, wClass, twObjectIx, Pod, aSupplementary);

         sDiff.clear ();
         if (wClass != Decoded.wClass)                                                                  sDiff += "wClass ";
         if (twObjectIx != Decoded.twObjectIx)                                                          sDiff += "twObjectIx ";
         if (std::memcmp (&Pod.Type,      &Decoded.Pod.Type,      sizeof (Pod.Type)) != 0)              sDiff += "Type ";
         if (std::memcmp (&Pod.Resource,  &Decoded.Pod.Resource,  sizeof (Pod.Resource)) != 0)          sDiff += "Resource ";
         if (std::memcmp (&Pod.Transform, &Decoded.Pod.Transform, sizeof (Pod.Transform)) != 0)         sDiff += "Transform ";
         if (std::memcmp (&Pod.Bound,     &Decoded.Pod.Bound,     sizeof (Pod.Bound)) != 0)             sDiff += "Bound ";
         if (asWarnings.empty () && std::memcmp (&Pod.Name, &Decoded.Pod.Name, sizeof (Pod.Name)) != 0) sDiff += "Name ";

         return sDiff.empty ();
      }
#endif // WORLDFORGE_LINK_SNEEZE
   }
}
