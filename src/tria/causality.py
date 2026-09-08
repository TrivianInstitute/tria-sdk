"""One causal ambiguity calculation shared through the derived projection."""
def ambiguous_permissions(events):
    by_id = {e.event_id: e for e in events}
    def precedes(left, right):
        if left.actor_id == right.actor_id and left.actor_sequence < right.actor_sequence:
            return True
        pending = list(right.causal_parents)
        seen = set()
        while pending:
            eid = pending.pop()
            if eid == left.event_id:
                return True
            if eid not in seen:
                seen.add(eid)
                parent = by_id.get(eid)
                if parent is not None:
                    pending.extend(parent.causal_parents)
        return False
    latest = {}
    for event in events:
        if event.event_type in {'PermissionGranted', 'PermissionRevoked'}:
            p = event.payload
            key = (p['grantee'], p['resource'], p['capability'])
            latest.setdefault(key, {})[event.event_type] = event
    return frozenset(key for key, pair in latest.items()
        if len(pair) == 2 and not precedes(pair['PermissionGranted'], pair['PermissionRevoked'])
        and not precedes(pair['PermissionRevoked'], pair['PermissionGranted']))
