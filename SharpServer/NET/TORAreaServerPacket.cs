using System;

namespace NexusToRServer.NET
{
    // Both halves must match the handles exchanged during area-service attach.
    public abstract class TORAreaServerPacket : TORGameServerPacket
    {
        public UInt16 ClientAreaServiceID { get; set; }

        protected void WriteAreaComponent()
        {
            if (ClientAreaServiceID == 0)
                throw new InvalidOperationException("Area packet requires an attached client area service.");
            WriteUInt16(0x65B3);
            WriteUInt16(ClientAreaServiceID);
        }
    }
}
