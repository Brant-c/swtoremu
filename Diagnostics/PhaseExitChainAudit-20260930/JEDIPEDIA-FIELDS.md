# Jedipedia field and reference cross-check

Reader: https://swtor.jedipedia.net/reader, loaded April 1.2.0 archive. Checked
HeroScript, class inheritance, field data types, attribute metadata and reverse
references. DOM history shows last relevant definition change 1.1.0; the history
heading is not evidence that the loaded script archive changed to 1.1.0.

`phsClassPhasedInstance`, class ID 4611686090226269993, inherits
`phsPhasedInstance`. Client script 14988018442410894040 and server script
14988238376313749512 are distinct entries. A server script ID listed by the DOM
does not mean its body is present in the client archive.

Field `phsPhasedInstanceToTrigger`:

- Field ID 4611686071571749259, name hash E6C5680B.
- Type: LookupList indexed by ID of NodeRef of TriggerInstance.
- Declared in client.gom; shared with server DOM; attribute bitset zero.
- In the inherited class field table: Not stored.
- Reverse references: phsPhasedInstance.OnReplicationNodeCreate (client script
  14988075381240041184), phsOracle._SetGatewayState (14988158324020229042).

Related inherited fields: `phsGatewayList` is List of NodeRef of HBNode;
`hydPrimaryScriptId` is Int; both shown Not stored. `phsExitAreaID` is ID,
Not stored; `phsRepublicExitAreaID` is ID, Stored. These labels describe recorded
DOM/prototype storage metadata, not a complete network wire schema or proof of
live values. Shared DOM declaration alone does not imply a field is replicated.

Reader HeroScript for OnReplicationNodeCreate independently confirms:

1. Register instance under phsNameID.
2. Enumerate type-4 triggers; compare stable identifier of TriggerParam against
   phsNameID; append gateway and attach client gateway clone.
3. Enumerate type-3 triggers with the same name match; GlomClass TriggerInstance
   if needed, then store the trigger in phsPhasedInstanceToTrigger.
4. Initialize conditional Hydra if configured and primary script map absent.
5. Refresh gateway if local player exists.

Its OnReplicationNodeUpdate body only iterates changed IDs with no displayed
work. Thus the reviewed scripts populate the physical trigger lookup at node
creation, not at membership exit. Whether every relevant room trigger existed
and was enumerated at that moment is unresolved. Do not infer a registration
race or repair ordering without verifying the native enumeration and runtime
object lifecycle.

Primary confidence: Client-derived. No runtime behavior changed. This supports
checking creation-time binding before inventing a network field update. It does
not identify the actual blocking collider.
