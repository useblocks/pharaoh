Decisions
=========

.. decision:: Use CAN bus for brake pedal sensor
   :id: DEC_001
   :status: accepted
   :decides: REQ_001, SPEC_001
   :decided_by: engineer-a
   :alternatives: SPI at 1MHz; Direct analog input
   :rationale: CAN bus provides noise immunity required for safety-critical braking and reuses existing vehicle bus

   Selected CAN bus over SPI and direct analog based on EMC requirements
   and existing bus infrastructure in the brake ECU.

.. decision:: Use proportional algorithm for force distribution
   :id: DEC_002
   :status: accepted
   :decides: REQ_002, SPEC_002
   :decided_by: claude
   :alternatives: Fixed ratio front/rear; Adaptive ML-based distribution
   :rationale: Proportional distribution is deterministic and certifiable under ISO 26262 ASIL-D

   Proportional axle-load-based distribution chosen over fixed ratio (insufficient for varying loads)
   and ML-based (not certifiable at ASIL-D).
