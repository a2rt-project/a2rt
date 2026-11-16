"""Check the current documentation snapshot and illustrative configuration.

These checks are not a wire-protocol validator or runtime conformance suite.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import re
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = ROOT / 'protocol'


def main():
    source = json.loads((PROTOCOL / 'SOURCE.json').read_text())
    assert source['status'] == 'architecture-draft'
    assert source['wire_protocol_version'] is None
    for name, digest in source['files'].items():
        assert hashlib.sha256((PROTOCOL / name).read_bytes()).hexdigest() == digest['local_sha256'], f'Source snapshot changed: {name}'
    assert not list(PROTOCOL.glob('schemas/*')), 'No released machine schema for this architecture'
    assert not (ROOT / 'protocol-legacy').exists(), 'Only the current architecture is published'
    for page in PROTOCOL.rglob('*.md'):
        assert not re.search(r'a2rt-legacy|0\.2\.0-draft|canvas_event_loop', page.read_text()), f'Outdated protocol content: {page}'
        for block in re.findall(r'```json\s*\n(.*?)\n```', page.read_text(), re.S):
            json.loads(block)
    chapter = (PROTOCOL / '01-clock-sync-group-track-model.md').read_text()
    config = json.loads(re.search(r'```json\s*\n(.*?)\n```', chapter, re.S)[1])
    clocks = {clock['clock_id']: clock for clock in config['clocks']}
    assert len(clocks) == len(config['clocks']) and 'root' in clocks
    root = clocks['root']
    assert 'parent_clock_id' not in root and root['frequency_hz'] > 0
    for name in ('standard_frame_bytes', 'standard_frames_per_tick'):
        assert type(root[name]) is int and root[name] > 0
    mappings = {'root': (1, 0)}

    def clock_mapping(name, visiting=()):
        assert name in clocks and name not in visiting, 'Missing parent or cycle'
        if name in mappings:
            return mappings[name]
        clock = clocks[name]
        period, offset = clock['period_parent_ticks'], clock['offset_parent_ticks']
        assert type(period) is int and period > 0
        assert type(offset) is int and offset >= 0
        parent_period, parent_offset = clock_mapping(clock['parent_clock_id'], (*visiting, name))
        mappings[name] = (parent_period * period, parent_offset + parent_period * offset)
        return mappings[name]

    for name in clocks:
        clock_mapping(name)
    groups = {group['sync_group_id']: group for group in config['sync_groups']}
    assert len(groups) == len(config['sync_groups'])
    sustained = Fraction(0)
    for group in groups.values():
        assert not {'role', 'direction'} & group.keys()
        period, offset = clock_mapping(group['clock_id'])
        start = group.get('start_tick', 0)
        assert type(start) is int and start >= 0
        assert type(offset + start * period) is int
        limits = group['limits']
        assert type(limits['max_frame_units']) is int and limits['max_frame_units'] > 0
        sustained += Fraction(limits['max_frame_units'], period)
        queues = limits['receiver_queues']
        assert len({q['receiver_id'] for q in queues}) == len(queues)
        assert all(type(q['max_pending_frames']) is int and q['max_pending_frames'] > 0 for q in queues)
    assert sustained <= root['standard_frames_per_tick'], 'Illustrative sustained total exceeds root capacity'
    formats = {fmt['format_id']: fmt for fmt in config['formats']}
    assert len(formats) == len(config['formats'])
    for fmt in formats.values():
        assert fmt['media_type'] and isinstance(fmt['constraints'], dict)
        assert not {'schema', 'schema_ref'} <= fmt['constraints'].keys()
    tracks = config['tracks']
    assert len({t['track_id'] for t in tracks}) == len(tracks)
    system = [track for track in tracks if track['role'] == 'system']
    assert len(system) == 1 and system[0]['direction'] == 'input'
    for track in tracks:
        assert track['sync_group_id'] in groups and track['format_id'] in formats
        assert track['source_binding'] and 'clock_id' not in track
        receivers = {q['receiver_id'] for q in groups[track['sync_group_id']]['limits']['receiver_queues']}
        expected = {'model_adapter'} if track['direction'] == 'input' else {'environment_adapter'}
        if track['direction'] == 'bidirectional':
            expected = {'model_adapter', 'environment_adapter'}
        assert expected <= receivers
    print(f"Current source snapshot and configuration illustration passed ({len(clocks)} clocks, {len(groups)} groups, {len(tracks)} tracks). Not runtime conformance.")
    check_canvas_profile()


def check_canvas_profile():
    """Validate published machine files and references, not mock runtime behavior."""
    directory = PROTOCOL / 'profiles/canvas-realtime'
    profile = json.loads((directory / 'profile.json').read_text())
    session = json.loads((directory / 'session.json').read_text())
    assert session['profile_id'] == profile['profile_id'] == 'canvas.excalidraw.realtime'
    assert session['profile_version'] == profile['version'] == '0.3.0-draft'
    assert session['binding_id'] == profile['binding_id'] == 'canvas.a2rt.mock.v2'
    schemas = {p.name: json.loads(p.read_text()) for p in directory.glob('schemas/*.json')}
    assert len(schemas) == 6
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    for tool in profile['tools']:
        Draft202012Validator.check_schema(tool['inputSchema'])

    def check_references(value):
        if isinstance(value, dict):
            if 'schema_ref' in value:
                assert (directory / value['schema_ref']).is_file(), value['schema_ref']
            for child in value.values():
                check_references(child)
        elif isinstance(value, list):
            for child in value:
                check_references(child)

    check_references(profile)
    check_references(session)
    clocks = {clock['clock_id']: clock for clock in session['clocks']}
    assert clocks['root']['frequency_hz'] == 1000
    for name, period in [('interaction', 100), ('notifications', 10)]:
        assert clocks[name]['parent_clock_id'] == 'root'
        assert clocks[name]['period_parent_ticks'] == period and clocks[name]['offset_parent_ticks'] == 0
    groups = {group['sync_group_id']: group for group in session['sync_groups']}
    formats = {fmt['format_id']: fmt for fmt in session['formats']}
    tracks = session['tracks']
    assert len(groups) == 2 and len(tracks) == len({track['track_id'] for track in tracks}) == 7
    assert [(t['track_id'], t['direction']) for t in tracks if t['role'] == 'system'] == [('system', 'input')]
    assert sum(Fraction(g['limits']['max_frame_units'], clocks[g['clock_id']]['period_parent_ticks']) for g in groups.values()) <= clocks['root']['standard_frames_per_tick']
    for track in tracks:
        assert track['format_id'] in formats and track['sync_group_id'] in groups
        assert track['source_binding']['source_ids']
        group = groups[track['sync_group_id']]
        receivers = {q['receiver_id'] for q in group['limits']['receiver_queues'] if q['max_pending_frames'] > 0}
        assert ('model' if track['direction'] == 'input' else 'environment') in receivers
    assert formats['audio']['media_type'] == 'audio/L16'
    assert formats['audio']['constraints']['rate'] == 24000 and formats['audio']['constraints']['channels'] == 1
    print('Canvas Realtime: Profile/session references, 7 tracks, 2 groups, and 6 schemas passed. Not runtime conformance.')


if __name__ == '__main__':
    main()
