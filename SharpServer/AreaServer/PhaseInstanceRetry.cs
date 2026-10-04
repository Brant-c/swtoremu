using System;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.AreaServer
{
    /// <summary>
    /// Diagnostic re-emission of the captured phase-instance transaction.
    ///
    /// The 2026-09-28 offline audit proved that the doorway gateway never
    /// attaches because no engine trigger of type INSTANCE_GATEWAY is present
    /// in the replicated area-object stream, so
    /// phsPhasedInstance.OnReplicationNodeCreate finds no match in
    /// GetTriggersByType(4). The one remaining question is whether the client
    /// materialises those engine trigger nodes from its own area assets (and
    /// simply populates the registry later than the startup transaction) or
    /// expects the server to replicate them.
    ///
    /// Re-running the create handler is what matters: GetTriggersByType(4) is
    /// only consulted inside phsPhasedInstance.OnReplicationNodeCreate, and the
    /// engine does not re-fire that callback for a node that already exists.
    /// Re-sending the captured transaction therefore proved nothing.
    ///
    /// The first version of this probe was invalid three ways at once: its
    /// "fresh" node ID 0x1AC688C980 is a live CRT1 object, so it sent an update
    /// and no create handler ran; it reused CRT11's stream id, which the startup
    /// bundle had already delivered, so the client could discard it as a
    /// duplicate stream; and re-sending an existing node cannot re-fire a
    /// create handler regardless.
    ///
    /// This now emits a *duplicate* phsClassPhasedInstance node from the same
    /// captured template, on a node ID and a stream id that are proven unused
    /// across every .acrt (see Diagnostics/Generate-PhaseInstanceDuplicate.py,
    /// which refuses to write unless both proofs pass). A new node guarantees a
    /// real create handler run.
    ///
    /// If the trigger registry holds the INSTANCE_GATEWAY doorway by then,
    /// _AttachGatewayTrigger runs, a phsGatewayFx portal appears at the phase
    /// door, and entering it produces a phase RPC or an on-screen message. If
    /// nothing appears, the engine trigger is absent client-side and must come
    /// from server-side area-object streaming.
    ///
    /// Disabled unless SWTOR_PHASE_INSTANCE_RETRY is set to a positive number
    /// of seconds. It never edits fixtures and never destroys anything.
    /// </summary>
    internal static class PhaseInstanceRetry
    {
        private static readonly int IntervalSeconds = ReadInt("SWTOR_PHASE_INSTANCE_RETRY", 0);
        private static readonly int FirstDelaySeconds = ReadInt("SWTOR_PHASE_INSTANCE_RETRY_START", 25);
        private static readonly int CrtID = ReadInt("SWTOR_PHASE_INSTANCE_RETRY_CRT", 18);
        private static readonly int MaxSends = ReadInt("SWTOR_PHASE_INSTANCE_RETRY_MAX", 8);

        private static int _lastSendTick;
        private static int _sendCount;
        private static bool _announced;

        private static int ReadInt(string name, int fallback)
        {
            string raw = Environment.GetEnvironmentVariable(name);
            int value;
            if (String.IsNullOrEmpty(raw) || !Int32.TryParse(raw, out value))
                return fallback;
            return value;
        }

        internal static void Tick(TORGameClient client)
        {
            if (client == null || IntervalSeconds <= 0)
                return;

            if (!_announced)
            {
                _announced = true;
                Log.Write(LogLevel.Warning,
                    "PhaseInstanceRetry: enabled, CRT {0}, first delay {1}s, interval {2}s, max {3}.",
                    CrtID, FirstDelaySeconds, IntervalSeconds, MaxSends);
            }

            if (_sendCount >= MaxSends)
                return;
            if (client.AreaServiceID == 0 || client.ActiveCharacter == null)
                return;

            int now = Environment.TickCount;
            int due = _sendCount == 0
                ? FirstDelaySeconds * 1000
                : IntervalSeconds * 1000;
            if (_lastSendTick != 0 && now - _lastSendTick < due)
                return;
            if (_lastSendTick == 0)
            {
                // First opportunity: record the reference point and wait.
                _lastSendTick = now;
                return;
            }

            _lastSendTick = now;
            _sendCount++;

            try
            {
                client.SendPacket(new AreaClientReplicationTransaction(
                    client._area ?? string.Empty,
                    client._areaID ?? string.Empty,
                    client._areaCode ?? string.Empty,
                    CrtID,
                    client.ActiveCharacter._id));
                Log.Write(LogLevel.Warning,
                    "PhaseInstanceRetry: duplicate-instance create {0}/{1} sent via CRT {2}; a fresh node forces OnReplicationNodeCreate to re-run.",
                    _sendCount, MaxSends, CrtID);
            }
            catch (Exception error)
            {
                Log.Write(LogLevel.Warning,
                    "PhaseInstanceRetry: duplicate-instance create {0} failed: {1}",
                    _sendCount, error.Message);
                _sendCount = MaxSends;
            }
        }
    }
}
