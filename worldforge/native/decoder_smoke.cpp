// worldforge/native/decoder_smoke.cpp
//
// Runs the decoder over every worldforge/out/<slug>/sneeze-mount-plan.json listed in
// worldforge/out/index.json and checks what it produced. It links only the decoder (header-only
// nlohmann/json, POD types). It does not link Sneeze, Map or RMAP, and it does not mount or render.
// It proves the decoder's own logic on the real plans, nothing more.
//
//   decoder_smoke <repo-root>                      one final line; exit 1 on any decode error or failed invariant
//   decoder_smoke <repo-root> --dump-branch <slug>   prints that plan as a Sneeze fabric-node branch (MSF "Data" route)

#include "rmcobject_decoder.hpp"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>

namespace
{
   bool Load (const std::string& sPath, nlohmann::json& j)
   {
      std::ifstream f (sPath, std::ios::binary);
      if (!f)
         return false;
      std::stringstream ss;
      ss << f.rdbuf ();
      j = nlohmann::json::parse (ss.str (), nullptr, false);
      return !j.is_discarded ();
   }

   // FNV-1a 64 over the decoded native values, so two runs (or two machines) can be compared.
   void Fnv (uint64_t& h, const void* p, size_t n)
   {
      const unsigned char* pb = static_cast<const unsigned char*> (p);
      for (size_t i = 0; i < n; i++)
      {
         h ^= pb[i];
         h *= 0x100000001b3ull;
      }
   }

   double Num (const nlohmann::json& a, size_t i) { return a.at (i).get<double> (); }
}

int main (int argc, char** argv)
{
   if (argc < 2)
   {
      std::printf ("decoder smoke: FAIL usage: decoder_smoke <repo-root>\n");
      return 1;
   }

   const std::string sRoot = argv[1];
   nlohmann::json    jIndex;

   if (argc == 4 && std::strcmp (argv[2], "--dump-branch") == 0)
   {
      nlohmann::json jPlan;
      if (!Load (sRoot + "/worldforge/out/" + argv[3] + "/sneeze-mount-plan.json", jPlan))
      {
         std::printf ("decoder smoke: FAIL no plan for %s\n", argv[3]);
         return 1;
      }
      std::vector<std::string> asErrors, asWarnings;
      nlohmann::json           jBranch = WORLDFORGE::NATIVE::MountPlanToBranch (jPlan, asErrors, asWarnings);
      for (const std::string& e : asErrors)
         std::fprintf (stderr, "error: %s\n", e.c_str ());
      std::printf ("%s\n", jBranch.dump (1).c_str ());
      return asErrors.empty () ? 0 : 1;
   }

   if (!Load (sRoot + "/worldforge/out/index.json", jIndex) || !jIndex.contains ("worlds"))
   {
      std::printf ("decoder smoke: FAIL cannot read worldforge/out/index.json\n");
      return 1;
   }

   size_t   nPlans = 0, nNodes = 0, nDecodeErrors = 0, nPlanErrors = 0, nInvariant = 0;
   size_t   nClamped = 0, nFolded = 0, nResource = 0;
   uint64_t qwPod  = 0xcbf29ce484222325ull;
   uint64_t qwJson = 0xcbf29ce484222325ull;

   for (const nlohmann::json& w : jIndex["worlds"])
   {
      const std::string sSlug = w.value ("slug", "");
      nlohmann::json    jPlan;

      if (!Load (sRoot + "/worldforge/out/" + sSlug + "/sneeze-mount-plan.json", jPlan))
      {
         std::fprintf (stderr, "%s: plan missing or unparsable\n", sSlug.c_str ());
         nPlanErrors++;
         continue;
      }
      nPlans++;

      std::vector<std::string>                           asPlanErrors;
      std::vector<WORLDFORGE::NATIVE::RMCOBJECT_DECODED> aDecoded = WORLDFORGE::NATIVE::MountPlanDecode (jPlan, asPlanErrors);

      for (const std::string& s : asPlanErrors)
         std::fprintf (stderr, "%s: %s\n", sSlug.c_str (), s.c_str ());
      nPlanErrors += asPlanErrors.size ();

      const nlohmann::json& aNode = jPlan["nodes"];
      for (size_t i = 0; i < aDecoded.size (); i++)
      {
         const WORLDFORGE::NATIVE::RMCOBJECT_DECODED& d = aDecoded[i];
         const nlohmann::json&                        s = aNode[i];

         nNodes++;
         for (const std::string& e : d.asErrors)
         {
            std::fprintf (stderr, "%s %s: %s\n", sSlug.c_str (), d.sCardId.c_str (), e.c_str ());
            nDecodeErrors++;
         }
         for (const std::string& wn : d.asWarnings)
            if (wn.rfind ("name clamped", 0) == 0)
               nClamped++;

         // Invariants on the native values.
         bool bOk = true;
         bOk = bOk && d.Pod.Name.wsName[WORLDFORGE::NATIVE::kNAME_UNITS_MAX] == 0;              // NUL kept
         bOk = bOk && (d.wClass == RMAP::MAP::MAP_OBJECT_CLASS_TERRESTRIAL || d.wClass == RMAP::MAP::MAP_OBJECT_CLASS_PHYSICAL);
         bOk = bOk && d.Pod.Type.bSubtype != 255;                                               // not an attachment point
         bOk = bOk && d.Pod.Resource.sReference[sizeof (d.Pod.Resource.sReference) - 1] == '\0';

         const nlohmann::json& t = s["transform"]["translation"];
         bOk = bOk && d.Pod.Transform.d3Position[0] ==  Num (t, 0)                             // Y-up -> Z-up
                   && d.Pod.Transform.d3Position[1] == -Num (t, 2)
                   && d.Pod.Transform.d3Position[2] ==  Num (t, 1);

         const nlohmann::json& sc = s["transform"]["scale"];
         bOk = bOk && d.Pod.Transform.d3Scale[0] == Num (sc, 0)
                   && d.Pod.Transform.d3Scale[1] == Num (sc, 2)
                   && d.Pod.Transform.d3Scale[2] == Num (sc, 1);

         const double* q = d.Pod.Transform.d4Rotation;
         bOk = bOk && std::fabs (std::sqrt (q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]) - 1.0) <= WORLDFORGE::NATIVE::kQUAT_TOLERANCE;

         if (s["resource"].is_object ())
         {
            nResource++;
            bOk = bOk && s["resource"]["sReference"].get<std::string> () == d.Pod.Resource.sReference;
         }
         else bOk = bOk && d.Pod.Resource.sReference[0] == '\0';

         if (!bOk)
         {
            std::fprintf (stderr, "%s %s: invariant failed\n", sSlug.c_str (), d.sCardId.c_str ());
            nInvariant++;
         }

         Fnv (qwPod, &d.wClass, sizeof (d.wClass));
         Fnv (qwPod, &d.twObjectIx, sizeof (d.twObjectIx));
         Fnv (qwPod, &d.Pod, sizeof (d.Pod));
      }

      // The MSF "Data" route: the whole plan as one nested branch.
      std::vector<std::string> asErrors, asWarnings;
      nlohmann::json           jBranch = WORLDFORGE::NATIVE::MountPlanToBranch (jPlan, asErrors, asWarnings);

      if (!asErrors.empty () || !jBranch.is_object ())
      {
         std::fprintf (stderr, "%s: branch build failed\n", sSlug.c_str ());
         nPlanErrors++;
      }
      for (const std::string& wn : asWarnings)
         if (wn.rfind ("json route:", 0) == 0)
            nFolded++;

      const std::string sDump = jBranch.dump ();
      Fnv (qwJson, sDump.data (), sDump.size ());
   }

   const bool bPass = (nPlans == jIndex["worlds"].size ()) && nDecodeErrors == 0 && nPlanErrors == 0 && nInvariant == 0;

   std::printf ("decoder smoke: %s %zu plans, %zu nodes, %zu decode errors, %zu plan errors, %zu invariant failures, "
                "%zu resource nodes, %zu names clamped to 47 UTF-16 units, %zu json-route names ASCII-folded, "
                "pod fnv1a64 %016llx, branch fnv1a64 %016llx\n",
                bPass ? "PASS" : "FAIL", nPlans, nNodes, nDecodeErrors, nPlanErrors, nInvariant, nResource, nClamped, nFolded,
                static_cast<unsigned long long> (qwPod), static_cast<unsigned long long> (qwJson));

   return bPass ? 0 : 1;
}
