using System;

namespace NexusToRServer.AreaServer
{
    // Tython compatibility detector, not a general HeroEngine trigger runtime.
    // Captured authored INSTANCE_GATEWAY position: X=-63.6167984009.
    // Existing corridor is retained. Axis-aligned crossing and 0.05 hysteresis
    // are emulator policy; native rotated trigger-volume semantics are unproven.
    internal sealed class RetreatGatewayState
    {
        internal const float GatewayX = -63.6167984009f;
        private const float Margin = 0.05f;
        private bool hasPrevious, outside;
        private float previousX, previousY, previousZ;

        // +1 exit, -1 enter, 0 no membership change. Initial captured state is inside.
        internal int Observe(float x, float y, float z)
        {
            if (!Finite(x) || !Finite(y) || !Finite(z)) return 0;
            int change = 0;
            float boundary = GatewayX + (outside ? -Margin : Margin);
            bool crossed = hasPrevious && (outside
                ? previousX > boundary && x <= boundary
                : previousX < boundary && x >= boundary);
            if (crossed)
            {
                // Evaluate the segment at the plane, so a fast diagonal step
                // cannot fire just because its endpoint happens to be in range.
                float t = (boundary - previousX) / (x - previousX);
                float yAtPlane = previousY + (y - previousY) * t;
                float zAtPlane = previousZ + (z - previousZ) * t;
                if (yAtPlane > -8f && yAtPlane < -5f && zAtPlane > -130f && zAtPlane < -124f)
                {
                    change = outside ? -1 : 1;
                    outside = !outside;
                }
            }
            hasPrevious = true; previousX = x; previousY = y; previousZ = z;
            return change;
        }

        private static bool Finite(float value) { return !Single.IsNaN(value) && !Single.IsInfinity(value); }
    }
}
