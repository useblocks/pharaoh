Specifications
==============

.. spec:: Brake pedal sensor interface
   :id: SPEC_001
   :status: open
   :links: REQ_001

   The brake pedal sensor shall use CAN bus at 500kbps.
   Signal update rate: 10ms.

.. spec:: Force distribution algorithm
   :id: SPEC_002
   :status: open
   :links: REQ_002

   Electronic brake force distribution using wheel speed sensors.
   Algorithm: proportional distribution based on axle load.

.. spec:: Emergency detection logic
   :id: SPEC_003
   :status: open
   :links: REQ_003

   Deceleration threshold detection using IMU sensor data.
   Sampling rate: 1kHz. Trigger threshold: 8m/s² sustained for 50ms.
