// worldforge/native/rmcobject_decoder.hpp
//
// Decodes one node spec from worldforge/out/<slug>/sneeze-mount-plan.json into the native values
// Sneeze consumes when it builds a scene node. Written against these cloned headers:
//   MetaversalCorp/Sneeze  0008d08bc46546a29a93b447f3b173202358b69a
//   MetaversalCorp/Map     0e6d26ac34f4627baf86c333062a3981a6c40742
//   MetaversalCorp/RMAP    0fd7efba6febda9dc97a9f629732a380ef7f2dc7
// Every field below has a file:line citation in worldforge/native/RMCOBJECT_MAPPING.md.
//
// About the name "RMCOBJECT". At these commits "RMCOBJECT" is not one C++ struct:
//   * Sneeze's docs call the flat wire form of a SOM node an RMCOBJECT (RmcObject.h:18-21). In code,
//     that form is the triple (uint16_t wClass, uint64_t twObjectIx, RMAP::MAP::MAP_OBJECT_POD),
//     which is what SNEEZE::MOCelestial_FromJson writes (RmcObject.h:44) and what
//     RMAP::MAP::MAP_OBJECT::Create takes (Map_Object.h:171). CONTAINER::Node_Root and Node_Open
//     take the resulting RMAP::MAP::MAP_OBJECT* (Container.h:77-78).
//   * RMAP::MAP::RMCOBJECT (Map.h:95-128) is the map-service *model* class for celestial objects
//     (MODEL_OBJECT + MAP_OBJECT_CELESTIAL). Its only constructor takes an RMAP IREFERENCE and a
//     MEM::SOURCE (Map.h:122). A JSON spec cannot construct it, and Node_Open does not take it.
// So RmcObjectDecoder returns that triple, using the real types, plus the provenance that has no
// native slot (cardId, parentCardId, extras). Nothing here mounts or renders anything.
//
// Build: C++17. Include paths: <Sneeze>/include, <Sneeze>/src, <Map>/include, <RMAP>/RMAP/include,
// and nlohmann/json 3.11.3, the version Sneeze pins in deps/dependencies.json. See check_decoder.sh.
// Define WORLDFORGE_LINK_SNEEZE to also declare the parts that need the Map/Sneeze libraries:
// RmcObjectCreate, MountPlanApply and RmcObjectCrossCheck. Those compile with -fsyntax-only against
// the real headers, but they have never been linked or executed here.

#ifndef WORLDFORGE_NATIVE_RMCOBJECT_DECODER_HPP
#define WORLDFORGE_NATIVE_RMCOBJECT_DECODER_HPP

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>
#include <Map/Map_Object.h>   // RMAP::MAP::MAP_OBJECT_POD, MAP_OBJECT_CLASS, MAP_OBJECT

namespace WORLDFORGE
{
   namespace NATIVE
   {
      // Limits taken from the real field sizes, so a header change breaks the build instead of
      // silently moving the limit.
      constexpr size_t kNAME_UNITS_FIELD    = sizeof (RMAP::MAP::MAP_OBJECT_NAME::wsName) / sizeof (uint16_t);  // 48
      constexpr size_t kNAME_UNITS_MAX      = kNAME_UNITS_FIELD - 1;                                           // 47, plus a NUL
      constexpr size_t kREFERENCE_BYTES_MAX = sizeof (RMAP::MAP::MAP_OBJECT_RESOURCE::sReference) - 1;         // 127, plus a NUL
      constexpr size_t kRESNAME_BYTES_MAX   = sizeof (RMAP::MAP::MAP_OBJECT_RESOURCE::sName) - 1;              // 63, plus a NUL
      constexpr double kQUAT_TOLERANCE      = 1e-6;

      // Frame of the incoming spec. Every plan declares coordinateFrame.up = "Y" (glTF convention).
      // Sneeze's world is right-handed Z-up (GltfMesh.cpp:1827-1830, Compositor.cpp:1125-1126).
      enum class UP_AXIS { Y, Z };

      struct RMCOBJECT_DECODE_OPTIONS
      {
         UP_AXIS eUp = UP_AXIS::Y;   // Y: apply Rx(+90): (x,y,z) -> (x,-z,y), the same map GltfMesh.cpp:1827-1830 uses
      };

      struct RMCOBJECT_DECODED
      {
         // --- The native values CONTAINER consumes (Container.cpp:417-424) ---
         uint16_t                   wClass     = 0;    // RMAP::MAP::MAP_OBJECT_CLASS value (Map_Object.h:16-24)
         uint64_t                   twObjectIx = 0;    // SNEEZE::OBJECTIX_IDENTITY: the container assigns (Container.cpp:319-325)
         RMAP::MAP::MAP_OBJECT_POD  Pod        = {};   // Map_Object.h:124-134, 504 bytes

         // --- Provenance with no native slot (MAP_OBJECT_POD has no id/parent/extras field) ---
         std::string                sCardId;
         std::string                sParentCardId;     // empty for the plan root
         bool                       bRoot      = false;
         nlohmann::json             jExtras;

         std::vector<std::string>   asWarnings;        // lossy but legal (e.g. name clamped to 47 units)
         std::vector<std::string>   asErrors;          // the spec cannot be represented faithfully

         bool Ok () const { return asErrors.empty (); }
      };

      // One plan node -> native values. The default options assume the plan's declared Y-up frame.
      RMCOBJECT_DECODED RmcObjectDecoder (const nlohmann::json& spec);
      RMCOBJECT_DECODED RmcObjectDecoder (const nlohmann::json& spec, const RMCOBJECT_DECODE_OPTIONS& Options);

      // The whole plan, in plan order. Options come from plan.coordinateFrame.up. Plan-level errors go
      // into asErrors: missing or duplicate cardId, a root that is not first, a parent that is not earlier.
      std::vector<RMCOBJECT_DECODED> MountPlanDecode (const nlohmann::json& plan, std::vector<std::string>& asErrors);

      // The MSF "Data" route (NODE_MAP_DATA -> CONTAINER::Branch_Add -> SNEEZE::MOCelestial_FromJson):
      // one decoded node rendered back into the fabric-node JSON keys RmcObject.cpp:23-58 reads.
      // At Sneeze 0008d08 that decoder copies name *bytes* into UTF-16 units (RmcObject.cpp:136-145),
      // so each non-ASCII code point is written as '?' and noted in asWarnings.
      nlohmann::json RmcObjectNodeJson (const RMCOBJECT_DECODED& Decoded, std::vector<std::string>& asWarnings);

      // The whole plan as one nested branch: "aChildren" arrays (Container.cpp:54, 455-489).
      nlohmann::json MountPlanToBranch (const nlohmann::json& plan, std::vector<std::string>& asErrors, std::vector<std::string>& asWarnings);
   }
}

#ifdef WORLDFORGE_LINK_SNEEZE
namespace SNEEZE
{
   class CONTAINER;
}

namespace WORLDFORGE
{
   namespace NATIVE
   {
      // RMAP::MAP::MAP_OBJECT::Create (Map_Object.h:171). Returns nullptr for an unknown class
      // (Map/src/Map_Object.cpp:98-113). Needs the Map library to link.
      RMAP::MAP::MAP_OBJECT* RmcObjectCreate (const RMCOBJECT_DECODED& Decoded);

      // Where the plan root goes. bFabricRoot: CONTAINER::Node_Root(twFabricIx, ...), which needs a
      // fabric that has no root node yet (Container.cpp:290). Otherwise: Node_Open(qwComposed_Parent,
      // ...) under an existing node of the same container (Container.cpp:305-308).
      struct MOUNT_TARGET
      {
         bool     bFabricRoot       = true;
         uint64_t twFabricIx        = 0;
         uint64_t qwComposed_Parent = 0;
      };

      // NEVER EXECUTED IN THIS PROJECT. This is the mount sequence the plan asks for, written against
      // Container.h:77-80: parents first, each returned composed handle used as the children's parent,
      // and on failure the MAP_OBJECT is deleted the way Branch_Add does (Container.cpp:449, 484).
      // The caller owns thread safety: the container methods trust their caller (Scene.md:600-603), and
      // mutating while the compositor traverses is unsafe (Scene.md:563-591).
      bool MountPlanApply (SNEEZE::CONTAINER* pContainer, const MOUNT_TARGET& Target, const std::vector<RMCOBJECT_DECODED>& aDecoded, std::vector<uint64_t>& aqwHandle, std::vector<std::string>& asErrors);

      // Feeds RmcObjectNodeJson(Decoded) through SNEEZE::MOCelestial_FromJson (RmcObject.h:44) and compares
      // the result with Decoded. Needs the Sneeze library to link. Never executed here.
      bool RmcObjectCrossCheck (const RMCOBJECT_DECODED& Decoded, std::string& sDiff);
   }
}
#endif // WORLDFORGE_LINK_SNEEZE

#endif // WORLDFORGE_NATIVE_RMCOBJECT_DECODER_HPP
