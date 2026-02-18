import re, uuid, json, os, sys
from datetime import datetime
from typing import List, Dict, Any, Set
from logger_utils import log_debug, log_info, log_error, log_warning, log_exception, setup_logger


class ImprovedPlantUMLActivityParser:
    def __init__(self, plantuml_code: str, debug_options=None):
        self.code = plantuml_code
        self.debug = debug_options or {}
        self.tokens: List[Dict[str, Any]] = []
        self.ast: List[Dict[str, Any]] = []
        self.structure_contexts: List[Dict[str, Any]] = []
        self.parallel_contexts: List[Dict[str, Any]] = []
        self.elements: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, Any]] = []
        self.swimlanes: Dict[str, Dict[str, Any]] = {}
        self.title = ""
        self._id_map = {}
        self._added_edges: Set[str] = set()
        self._swimlane_order: List[str] = []

    # ---------------- PUBLIC ----------------
    def parse(self) -> Dict[str, Any]:
        self._tokenize()
        self._build_ast()
        self._materialize_elements()
        self._build_control_flow()
        self._inline_else_markers()
        self._transform_decision_end_to_merge()
        self._post_merge_cleanup()
        self._inject_synthetic_merge()
        self._consolidate_final_nodes()
        self._validate_and_repair()
        self._normalize_guards()
        self._compute_topology_metadata()
        return self._prepare_result()

    # ---------------- ID ----------------
    def _gen_id(self) -> str:
        return f"id_{uuid.uuid4().hex[:8]}"

    # ---------------- TOKENIZATION ----------------
    def _tokenize(self):
        patterns = [
            ('TITLE', r'^title\s+(.*)$'),
            ('SWIMLANE', r'^\|([^|]+)\|$'),
            ('PARTITION', r'^partition\s+"?([^\"]+)"?\s*(as\s+([A-Za-z0-9_]+))?\s*\{$'),
            ('ENDPARTITION', r'^\}$'),
            ('ACTIVITY', r'^:([^;]+);$'),
            ('COLOR_ACTIVITY', r'^#([A-Za-z0-9]+):([^;]+);$'),
            ('ARROW_ACTIVITY', r'^:([^;]+);\s*->\s*:([^;]+);$'),
            ('START', r'^start$'),
            ('END', r'^(stop|end)$'),
            ('KILL', r'^kill$'),
            ('DETACH', r'^detach$'),
            ('IF', r'^if\s*\((.*?)\)\s*then\s*\((.*?)\)$'),
            ('ELSE', r'^else(\s*\((.*?)\))?$'),
            ('ENDIF', r'^endif$'),
            ('WHILE', r'^while\s*\((.*?)\)\s*is\s*\((.*?)\)$'),
            ('ENDWHILE', r'^endwhile$'),
            ('REPEAT', r'^repeat$'),
            ('REPEAT_WHILE', r'^repeat while\s*\((.*?)\)$'),
            ('LOOP', r'^loop(?:\s+(.*))?$'),
            ('ENDLOOP', r'^endloop$'),
            ('FORK', r'^fork$'),
            ('FORK_AGAIN', r'^fork again$'),
            ('ENDFORK', r'^end fork$'),
            ('NOTE_START', r'^note\s+(left|right|top|bottom)(?:\s+of\s+([^:]+))?\s*(?::\s*(.*))?$'),
            ('NOTE_END', r'^end note$'),
            ('COMMENT', r"^'.*$"),
            ('DIRECTIVE', r'^![A-Za-z][A-Za-z0-9_]*(?:\s+.*)?$'),
            ('EMPTY', r'^\s*$'),
            ('STARTUML', r'^@startuml$'),
            ('ENDUML', r'^@enduml$')
        ]

        in_note = None
        note_buffer: List[str] = []

        for ln, raw in enumerate(self.code.splitlines(), start=1):
            stripped = raw.strip()

            if in_note:
                if re.match(r'^end note$', stripped):
                    text = '\n'.join(note_buffer).strip()
                    self.tokens.append({
                        'type': 'NOTE',
                        'position': in_note['pos'],
                        'note_text': text,
                        'attached_to': in_note.get('target'),
                        'line': in_note['line'],
                        'id': self._gen_id()
                    })
                    in_note = None
                    note_buffer = []
                else:
                    note_buffer.append(raw.rstrip('\n'))
                continue

            matched = False
            for name, pat in patterns:
                m = re.match(pat, stripped)
                if not m:
                    continue

                if name == 'NOTE_START':
                    direction = m.group(1)
                    target = (m.group(2) or '').strip() or None
                    inline_text = (m.group(3) or '').strip()
                    if inline_text:
                        self.tokens.append({
                            'type': 'NOTE',
                            'position': direction,
                            'note_text': inline_text,
                            'attached_to': target,
                            'line': ln,
                            'id': self._gen_id()
                        })
                    else:
                        in_note = {'pos': direction, 'line': ln, 'target': target}
                        note_buffer = []
                    matched = True
                    break

                if name == 'NOTE_END':
                    # end note bez otwartego bloku – ignoruj
                    matched = True
                    break

                tok = {'type': name, 'text': stripped, 'line': ln, 'id': self._gen_id()}
                if name == 'TITLE':
                    tok['title'] = m.group(1).strip()
                elif name == 'SWIMLANE':
                    tok['name'] = m.group(1).strip()
                elif name == 'ACTIVITY':
                    tok['activity'] = m.group(1).strip()
                elif name == 'COLOR_ACTIVITY':
                    tok['color'] = m.group(1).strip()
                    tok['activity'] = m.group(2).strip()
                elif name == 'ARROW_ACTIVITY':
                    tok['src_activity'] = m.group(1).strip()
                    tok['tgt_activity'] = m.group(2).strip()
                elif name == 'IF':
                    tok['condition'] = m.group(1).strip()
                    tok['then_label'] = m.group(2).strip() or 'tak'
                elif name == 'ELSE':
                    tok['else_label'] = (m.group(2) or m.group(3) or 'nie').strip()
                elif name == 'WHILE':
                    tok['condition'] = m.group(1).strip()
                    tok['while_value'] = m.group(2).strip()
                elif name == 'REPEAT_WHILE':
                    tok['condition'] = m.group(1).strip()
                elif name == 'LOOP':
                    tok['label'] = (m.group(1) or '').strip()
                self.tokens.append(tok)
                matched = True
                break

            if not matched and stripped and not stripped.startswith("'"):
                log_warning(f"Nierozpoznana linia {ln}: {stripped}")

        if in_note:
            text = '\n'.join(note_buffer).strip()
            self.tokens.append({
                'type': 'NOTE',
                'position': in_note['pos'],
                'note_text': text,
                'attached_to': in_note.get('target'),
                'line': in_note['line'],
                'id': self._gen_id()
            })

        if self.debug.get('parsing'):
            log_debug(f"Tokenów: {len(self.tokens)}")

    # ---------------- AST ----------------
    def _build_ast(self):
        self.parallel_contexts = []

        def _record_in_parallel(parent_stack, token):
            if token['type'] in ('FORK_AGAIN', 'ENDFORK'):
                return
            for ctx in reversed(parent_stack):
                if ctx.get('type') == 'parallel':
                    branch_idx = ctx.get('current_branch', 0)
                    branch = ctx['branches'][branch_idx]
                    if token not in branch:
                        branch.append(token)
                    break

        def _append_to_parent_context(parent_stack, token):
            if not parent_stack:
                return
            parent = parent_stack[-1]
            parent_type = parent.get('type')
            if parent_type == 'decision':
                branch = parent['then_branch'] if parent.get('current', 'then') == 'then' else parent['else_branch']
                branch.append(token)
            elif parent_type in ('repeat', 'loop'):
                parent['body'].append(token)
            _record_in_parallel(parent_stack, token)
        stack = []
        current_swimlane = None
        for tok in self.tokens:
            t = tok['type']
            if t in ('COMMENT', 'EMPTY', 'STARTUML', 'ENDUML', 'DIRECTIVE'):
                continue
            if t == 'TITLE':
                self.title = tok.get('title') or tok.get('text','').replace('title','',1).strip()
                continue
            if t == 'SWIMLANE':
                current_swimlane = tok.get('name')
                if current_swimlane and current_swimlane not in self.swimlanes:
                    self.swimlanes[current_swimlane] = {'activities': []}
                if current_swimlane and current_swimlane not in self._swimlane_order:
                    self._swimlane_order.append(current_swimlane)
                tok['swimlane'] = current_swimlane
                self.ast.append(tok)
                continue
            tok['swimlane'] = current_swimlane

            if t == 'IF':
                _append_to_parent_context(stack, tok)
                ctx = {
                    'type': 'decision',
                    'token': tok,
                    'then_branch': [],
                    'else_branch': [],
                    'current': 'then'
                }
                stack.append(ctx)
                self.structure_contexts.append(ctx)
                self.ast.append(tok)
                continue
            if t == 'ELSE':
                if stack and stack[-1]['type'] == 'decision':
                    stack[-1]['current'] = 'else'
                    tok['decision_id'] = stack[-1]['token']['id']
                self.ast.append(tok)
                continue
            if t == 'ENDIF':
                if stack and stack[-1]['type'] == 'decision':
                    tok['decision_id'] = stack[-1]['token']['id']
                    stack.pop()
                self.ast.append(tok)
                continue
            if t == 'REPEAT':
                _append_to_parent_context(stack, tok)
                ctx = {'type': 'repeat', 'token': tok, 'body': []}
                stack.append(ctx)
                self.structure_contexts.append(ctx)
                self.ast.append(tok)
                continue
            if t == 'REPEAT_WHILE':
                if stack and stack[-1]['type'] == 'repeat':
                    tok['repeat_id'] = stack[-1]['token']['id']
                    stack.pop()
                self.ast.append(tok)
                continue
            if t == 'LOOP':
                _append_to_parent_context(stack, tok)
                ctx = {'type': 'loop', 'token': tok, 'body': []}
                stack.append(ctx)
                self.structure_contexts.append(ctx)
                self.ast.append(tok)
                continue
            if t == 'ENDLOOP':
                if stack and stack[-1]['type'] == 'loop':
                    tok['loop_id'] = stack[-1]['token']['id']
                    stack.pop()
                self.ast.append(tok)
                continue
            if t == 'FORK':
                _append_to_parent_context(stack, tok)
                ctx = {
                    'type': 'parallel',
                    'fork_token': tok,
                    'branches': [[]],
                    'current_branch': 0,
                    'join_token': None
                }
                stack.append(ctx)
                self.parallel_contexts.append(ctx)
                self.ast.append(tok)
                continue
            if t == 'FORK_AGAIN':
                if stack and stack[-1].get('type') == 'parallel':
                    ctx = stack[-1]
                    ctx['current_branch'] += 1
                    ctx['branches'].append([])
                self.ast.append(tok)
                continue
            if t == 'ENDFORK':
                if stack and stack[-1].get('type') == 'parallel':
                    ctx = stack[-1]
                    ctx['join_token'] = tok
                    stack.pop()
                self.ast.append(tok)
                continue

            # Generic token
            self.ast.append(tok)
            if stack:
                top = stack[-1]
                if top['type'] == 'decision':
                    (top['then_branch'] if top['current'] == 'then' else top['else_branch']).append(tok)
                elif top['type'] in ('repeat', 'loop'):
                    top['body'].append(tok)
            _record_in_parallel(stack, tok)

        if stack:
            for ctx in stack:
                log_warning(f"Niezakończona struktura {ctx['type']} (linia {ctx['token']['line']})")

    # ---------------- ELEMENTS ----------------
    def _infer_status(self, elem: Dict[str,Any]):
        col = (elem.get('color') or '').lower()
        if 'green' in col:
            return 'success'
        if 'red' in col:
            return 'failure'
        return None

    def _materialize_elements(self):
        """
        Buduje słownik self.elements z tokenów AST.
        Każdy element otrzymuje: id, type, text/condition/label, swimlane, color, status, znaczniki pomocnicze.
        Nie tworzy krawędzi (tylko węzły). Elementy techniczne (repeat_end, decision_end itp.) zachowane.
        """
        for tok in self.ast:
            t = tok['type']
            elem = None

            if t == 'ACTIVITY':
                # tok['text'] np. ":Akcja;"
                raw = tok.get('text','')
                inner = raw.strip()[1:-1].rstrip(';').strip() if raw.startswith(':') else raw
                elem = {
                    'type': 'activity',
                    'text': inner,
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'COLOR_ACTIVITY':
                # zakładamy że tokenizacja uzupełnia tok['color'] i tok['activity']
                raw = tok.get('text','')
                # format np. "#Red:Akcja;"
                # jeśli parser nie ustawił pola activity, wyciągnij po pierwszym ':'
                if 'activity' in tok:
                    inner = tok['activity']
                else:
                    inner = raw.split(':',1)[1].rstrip(';').strip() if ':' in raw else raw
                elem = {
                    'type': 'activity',
                    'text': inner,
                    'color': tok.get('color'),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'ARROW_ACTIVITY':
                # Struktura ":A; -> :B;" – tworzymy oba węzły jeśli nie istnieją.
                src_raw, tgt_raw = tok.get('text').split('->')
                src_txt = src_raw.strip()[1:-1].rstrip(';').strip()
                tgt_txt = tgt_raw.strip()
                if tgt_txt.startswith(':'):
                    tgt_txt = tgt_txt[1:]
                if tgt_txt.endswith(';'):
                    tgt_txt = tgt_txt[:-1].strip()
                # źródło
                if not any(e.get('text') == src_txt and e.get('swimlane') == tok.get('swimlane') for e in self.elements.values()):
                    s_id = tok['id'] + "_src"
                    self.elements[s_id] = {
                        'id': s_id,
                        'type': 'activity',
                        'text': src_txt,
                        'swimlane': tok.get('swimlane'),
                        'synthetic': True
                    }
                # cel
                elem = {
                    'type': 'activity',
                    'text': tgt_txt,
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'START':
                sl = tok.get('swimlane')
                if self._swimlane_order:
                    sl = self._swimlane_order[0]
                elem = {'type': 'start', 'swimlane': sl}

            elif t in ('END','KILL','DETACH'):
                # KILL / DETACH mapowane na final (oznaczamy flagą)
                elem = {
                    'type': 'end',
                    'swimlane': tok.get('swimlane')
                }
                if t == 'KILL':
                    elem['kill'] = True
                if t == 'DETACH':
                    elem['detach'] = True

            elif t == 'IF':
                elem = {
                    'type': 'decision',
                    'condition': tok.get('condition',''),
                    'then_label': tok.get('then_label','tak'),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'ELSE':
                elem = {
                    'type': 'else_marker',
                    'decision_id': tok.get('decision_id'),
                    'else_label': tok.get('else_label','nie'),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'ENDIF':
                elem = {
                    'type': 'decision_end',
                    'decision_id': tok.get('decision_id'),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'REPEAT':
                elem = {
                    'type': 'repeat_start',
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'REPEAT_WHILE':
                elem = {
                    'type': 'repeat_end',
                    'repeat_id': tok.get('repeat_id'),
                    'condition': tok.get('condition',''),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'WHILE':
                elem = {
                    'type': 'loop_start',
                    'condition': tok.get('condition',''),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'ENDWHILE':
                elem = {
                    'type': 'loop_end',
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'LOOP':
                elem = {
                    'type': 'loop_start',
                    'label': tok.get('label',''),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'ENDLOOP':
                elem = {
                    'type': 'loop_end',
                    'loop_id': tok.get('loop_id'),
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'FORK':
                elem = {
                    'type': 'fork',
                    'variant': 'fork',
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'FORK_AGAIN':
                continue

            elif t == 'ENDFORK':
                elem = {
                    'type': 'join',
                    'swimlane': tok.get('swimlane')
                }

            elif t == 'NOTE':
                elem = {
                    'type': 'note',
                    'text': tok.get('note_text',''),
                    'position': tok.get('position'),
                    'swimlane': tok.get('swimlane'),
                    'attached_to': tok.get('attached_to')
                }
                prev_exec = self._previous_executable(tok['id'])
                if prev_exec:
                    elem['attached_to_id'] = prev_exec

            elif t in ('SWIMLANE','PARTITION','ENDPARTITION','TITLE'):
                continue  # nie tworzymy elementu

            if elem:
                elem['id'] = tok['id']
                # status na podstawie koloru
                if 'color' in elem:
                    elem['status'] = self._infer_status(elem)
                elem.setdefault('synthetic', False)
                self.elements[elem['id']] = elem
                

    # ---------------- FLOW BUILDING ----------------
    def _add_edge(self, s, t, label="", etype="control_flow"):
        if not s or not t or s == t:
            return
        norm_label = label.strip()
        if norm_label and not (norm_label.startswith('[') and norm_label.endswith(']')):
            norm_label = f'[{norm_label}]'
        key = f"{s}|{t}|{norm_label}"
        if key in self._added_edges:
            return
        self._added_edges.add(key)
        self.connections.append({
            'source_id': s, 'target_id': t,
            'label': norm_label, 'condition': norm_label,
            'type': etype,
            'source_type': self.elements.get(s, {}).get('type'),
            'target_type': self.elements.get(t, {}).get('type')
        })

    def _linear_sequence(self):
        seq = [tok for tok in self.ast if tok['type'] not in ('SWIMLANE', 'TITLE')]
        n = len(seq)
        parallel_membership = {}
        for pctx in self.parallel_contexts:
            fork_tok = pctx.get('fork_token') or {}
            fork_id = fork_tok.get('id')
            if not fork_id:
                continue
            for idx, branch in enumerate(pctx.get('branches', [])):
                for btok in branch:
                    parallel_membership[btok['id']] = (fork_id, idx)
        # zbuduj mapę: decision_id -> zbiór id w gałęzi else
        else_members = {}
        for ctx in self.structure_contexts:
            if ctx['type'] != 'decision':
                continue
            did = ctx['token']['id']
            else_ids = {t['id'] for t in ctx['else_branch']}
            else_members[did] = else_ids
        for i in range(n - 1):
            a_tok = seq[i]
            if a_tok['id'] not in self.elements:
                continue
            a_elem = self.elements[a_tok['id']]
            if a_elem['type'] in ('note', 'decision', 'else_marker', 'decision_end', 'repeat_end', 'loop_end'):
                continue
            # znajdź następny wykonywalny (pomijaj note, else_marker)
            j = i + 1
            b_tok = None
            while j < n:
                cand = seq[j]
                if cand['id'] in self.elements:
                    et = self.elements[cand['id']]['type']
                    if et not in ('note', 'else_marker'):
                        b_tok = cand
                        break
                j += 1
            if not b_tok:
                continue
            # nie mostkuj z THEN do pierwszego elementu ELSE tej samej decyzji
            # sprawdź czy a_tok leży w then_branch decyzji i b_tok w else_branch
            blocked = False
            for ctx in self.structure_contexts:
                if ctx['type'] != 'decision':
                    continue
                then_ids = {t['id'] for t in ctx['then_branch']}
                else_ids = else_members.get(ctx['token']['id'], set())
                if a_tok['id'] in then_ids and b_tok['id'] in else_ids:
                    blocked = True
                    break
            if blocked:
                continue
            a_mem = parallel_membership.get(a_tok['id'])
            b_mem = parallel_membership.get(b_tok['id'])
            if a_mem and b_mem and a_mem[0] == b_mem[0] and a_mem[1] != b_mem[1]:
                continue
            if a_mem and (not b_mem or a_mem[0] != b_mem[0]):
                continue
            b_elem = self.elements[b_tok['id']]
            if b_elem['type'] in ('decision_end', 'repeat_end', 'loop_end'):
                continue
            self._add_edge(a_tok['id'], b_tok['id'])

    def _refresh_connection_types(self):
        """Aktualizuje typy źródła i celu na krawędziach po zmianach elementów."""
        for c in self.connections:
            c['source_type'] = self.elements.get(c['source_id'], {}).get('type')
            c['target_type'] = self.elements.get(c['target_id'], {}).get('type')

    def _transform_decision_end_to_merge(self):
        """Konwersja decision_end -> merge (tag merge=True), usunięcie redundantnych (incoming<=1)."""
        incoming = {}
        outgoing = {}
        for c in self.connections:
            incoming[c['target_id']] = incoming.get(c['target_id'], 0) + 1
            outgoing[c['source_id']] = outgoing.get(c['source_id'], 0) + 1

        to_remove = []
        for eid, elem in list(self.elements.items()):
            if elem['type'] != 'decision_end':
                continue
            ic = incoming.get(eid, 0)
            prevs = [c for c in self.connections if c['target_id'] == eid]
            nexts = [c for c in self.connections if c['source_id'] == eid]

            if ic <= 1:
                # redundantny punkt – przepnij jeśli ma zarówno poprzedników jak i następniki
                if prevs and nexts:
                    for p in prevs:
                        for n in nexts:
                            self._add_edge(p['source_id'], n['target_id'])
                to_remove.append(eid)
            else:
                # zostaje jako merge
                elem['type'] = 'merge'
                elem['merge'] = True
                elem['role'] = 'merge'
                elem.pop('decision_id', None)

        if to_remove:
            self.connections = [
                c for c in self.connections
                if c['source_id'] not in to_remove and c['target_id'] not in to_remove
            ]
            for rid in to_remove:
                self.elements.pop(rid, None)

        # odśwież metadane krawędzi po zmianach typów
        self._refresh_connection_types()

    def _decision_edges(self):
        for ctx in self.structure_contexts:
            if ctx['type'] != 'decision':
                continue
            dec_id = ctx['token']['id']
            dec_elem = self.elements.get(dec_id)
            if not dec_elem:
                continue
            # THEN branch first executable
            then_target = self._first_executable(ctx['then_branch'])
            else_marker = self._find_else_marker(dec_id)
            else_target = self._first_executable(ctx['else_branch'])
            decision_end_id = self._find_decision_end(dec_id)

            if then_target:
                self._add_edge(dec_id, then_target, dec_elem.get('then_label','tak'))
            elif decision_end_id:
                self._add_edge(dec_id, decision_end_id, dec_elem.get('then_label','tak'))

            if else_marker:
                # explicit else marker as merge point → edge decision->else_marker with guard
                em_id = else_marker['id']
                self._add_edge(dec_id, em_id, else_marker.get('else_label','nie'))
                if else_target:
                    self._add_edge(em_id, else_target)
                elif decision_end_id:
                    self._add_edge(em_id, decision_end_id)
            else:
                if else_target:
                    self._add_edge(dec_id, else_target, 'nie')
                elif decision_end_id:
                    self._add_edge(dec_id, decision_end_id, 'nie')

            # Branch ends → decision_end
            if decision_end_id:
                last_then = self._last_executable(ctx['then_branch'])
                last_else = self._last_executable(ctx['else_branch'])
                if last_then and last_then != decision_end_id:
                    self._add_edge(last_then, decision_end_id)
                if last_else and last_else != decision_end_id:
                    self._add_edge(last_else, decision_end_id)

                # decision_end -> następny
                nxt = self._first_after_token(decision_end_id)
                if nxt:
                    self._add_edge(decision_end_id, nxt)

    def _parallel_edges(self):
        for ctx in self.parallel_contexts:
            fork_tok = ctx.get('fork_token')
            join_tok = ctx.get('join_token')
            fork_id = fork_tok['id'] if fork_tok else None
            join_id = join_tok['id'] if join_tok else None
            if not fork_id or fork_id not in self.elements:
                continue
            branches = ctx.get('branches', [])
            for branch in branches:
                first = self._first_executable(branch) if branch else None
                last = self._last_executable(branch) if branch else None
                if first:
                    self._add_edge(fork_id, first)
                elif join_id and join_id in self.elements:
                    self._add_edge(fork_id, join_id)
                if join_id and join_id in self.elements:
                    if last and last != join_id:
                        self._add_edge(last, join_id)
                    elif not first:
                        self._add_edge(fork_id, join_id)

    def _loop_edges(self):
        # repeat ... repeat while(condition)
        repeats = {e['id']: e for e in self.elements.values() if e['type']=='repeat_start'}
        for rs_id, rs in repeats.items():
            re_id = next((e['id'] for e in self.elements.values()
                          if e['type']=='repeat_end' and e.get('repeat_id')==rs_id), None)
            if not re_id:
                continue
            # pierwszy element ciała
            body_first = self._first_between(rs_id, re_id)
            if body_first:
                self._add_edge(rs_id, body_first)
            # OSTATNI element ciała -> repeat_end (BRAK w starej wersji)
            body_last = self._last_between(rs_id, re_id)
            if body_last and body_last != re_id:
                self._add_edge(body_last, re_id)
            cond = self.elements[re_id].get('condition','').strip()
            back_label = cond if cond else 'loop'
            exit_label = self._negate_condition_pretty(cond) if cond else 'exit'
            self._add_edge(re_id, rs_id, back_label, etype='loop_back')
            after = self._first_after_token(re_id)
            if after:
                self._add_edge(re_id, after, exit_label)

        # loop ... endloop (bez warunku)
        loops = {e['id']: e for e in self.elements.values() if e['type']=='loop_start'}
        for ls_id, ls in loops.items():
            le_id = next((e['id'] for e in self.elements.values()
                          if e['type']=='loop_end' and e.get('loop_id')==ls_id), None)
            if not le_id:
                continue
            body_first = self._first_between(ls_id, le_id)
            if body_first:
                self._add_edge(ls_id, body_first)
            body_last = self._last_between(ls_id, le_id)
            if body_last and body_last != le_id:
                self._add_edge(body_last, le_id)
            self._add_edge(le_id, ls_id, ls.get('label','loop') or 'loop', etype='loop_back')
            after = self._first_after_token(le_id)
            if after:
                self._add_edge(le_id, after)

    def _last_between(self, start_id, end_id):
        found = []
        started = False
        for tok in self.ast:
            if tok['id'] == start_id:
                started = True
                continue
            if tok['id'] == end_id:
                break
            if started and tok['id'] in self.elements:
                et = self.elements[tok['id']]['type']
                if et not in ('note',):
                    found.append(tok['id'])
        return found[-1] if found else None

    def _negate_condition_pretty(self, cond: str) -> str:
        """Heurystyczna negacja warunku do etykiety wyjścia pętli."""
        c = cond.strip()
        lower = c.lower()
        repl = [
            (" is false", " is true"),
            (" == false", " == true"),
            (" == false", " == true"),
            (" != true", " != false"),
            (" == True", " == False"),
            (" == true", " == false"),
            (" != False", " != True"),
            (" != false", " != true"),
        ]
        for a,b in repl:
            if lower.endswith(a):
                # zachowaj oryginalną wielkość liter poza wzorcem
                return c[:-len(a)] + b
        if lower.startswith("!"):
            return c[1:].strip()
        # fallback
        return f"NOT({c})"

    def _post_merge_cleanup(self):
        """Usuwa merge z incoming==1 i scala łańcuchy merge->merge."""
        changed = True
        while changed:
            changed = False
            # policz incoming/outgoing
            incoming = {}
            outgoing = {}
            for c in self.connections:
                incoming[c['target_id']] = incoming.get(c['target_id'], 0) + 1
                outgoing[c['source_id']] = outgoing.get(c['source_id'], 0) + 1
            # usuwaj merge o jednym wejściu
            to_remove = []
            for eid, e in list(self.elements.items()):
                if e['type'] == 'merge' and incoming.get(eid,0) <= 1:
                    prevs = [c for c in self.connections if c['target_id']==eid]
                    nexts = [c for c in self.connections if c['source_id']==eid]
                    if prevs and nexts:
                        for p in prevs:
                            for n in nexts:
                                self._add_edge(p['source_id'], n['target_id'])
                    to_remove.append(eid)
                    changed = True
            if to_remove:
                self.connections = [c for c in self.connections if c['source_id'] not in to_remove and c['target_id'] not in to_remove]
                for rid in to_remove:
                    self.elements.pop(rid, None)
            # scala merge->merge
            for c in list(self.connections):
                if self.elements.get(c['source_id'],{}).get('type')=='merge' and \
                   self.elements.get(c['target_id'],{}).get('type')=='merge':
                    # przepnij wszystkie wejścia pierwszego do drugiego
                    first = c['source_id']; second = c['target_id']
                    ins = [e for e in self.connections if e['target_id']==first]
                    for ie in ins:
                        self._add_edge(ie['source_id'], second, ie.get('label',''))
                    # oznacz pierwszy do usunięcia
                    to_remove_chain = [first]
                    self.connections = [e for e in self.connections if e is not c and e['source_id'] not in to_remove_chain and e['target_id'] not in to_remove_chain]
                    for rid in to_remove_chain:
                        self.elements.pop(rid, None)
                    changed = True
        self._refresh_connection_types()

    def _inject_synthetic_merge(self):
        # Szukamy par krawędzi z różnych źródeł (różne gałęzie tej samej decyzji) konwergujących w tym samym celu
        # bez węzła typu merge / decision_end pomiędzy.
        incoming_map = {}
        for c in self.connections:
            incoming_map.setdefault(c['target_id'], []).append(c)
        for target, inc in list(incoming_map.items()):
            # źródła z decyzji (2+) → brak istniejącego merge node typu 'merge'
            decision_sources = {c['source_id'] for c in inc if self.elements.get(c['source_id'],{}).get('type') in ('activity','decision')}
            if len(decision_sources) >= 2:
                # sprawdź czy target nie jest już merge / decision_end
                if self.elements.get(target,{}).get('type') in ('merge','decision_end','join'):
                    continue
                # wstaw merge przed target
                merge_id = self._gen_id()
                self.elements[merge_id] = {'id': merge_id, 'type': 'merge', 'synthetic': True}
                # przepnij źródła -> merge -> target
                to_add = []
                to_remove = []
                for c in inc:
                    to_remove.append(c)
                    to_add.append({'source_id': c['source_id'], 'target_id': merge_id, 'label': c['label'], 'condition': c['condition'],
                                'type': 'control_flow', 'source_type': c['source_type'], 'target_type': 'merge'})
                # usuń stare
                self.connections = [c for c in self.connections if c not in to_remove]
                # dodaj nowe krawędzie
                for c in to_add:
                    self._add_edge(c['source_id'], c['target_id'], c['label'].strip('[]'))
                # merge -> target
                self._add_edge(merge_id, target)

    def _build_control_flow(self):
        self._linear_sequence()
        self._parallel_edges()
        self._decision_edges()
        self._loop_edges()

    # ---------------- HELPERS (selection) ----------------
    def _find_else_marker(self, decision_id):
        for tok in self.ast:
            if tok['type']=='ELSE' and tok.get('decision_id')==decision_id:
                return tok
        return None

    def _find_decision_end(self, decision_id):
        for tok in self.ast:
            if tok['type']=='ENDIF' and tok.get('decision_id')==decision_id:
                return tok['id']
        return None

    def _first_executable(self, token_list):
        for t in token_list:
            if t['type'] in ('SWIMLANE','ELSE','ENDIF'):
                continue
            if t['id'] in self.elements and self.elements[t['id']]['type'] not in ('note',):
                return t['id']
        return None

    def _last_executable(self, token_list):
        for t in reversed(token_list):
            if t['type'] in ('SWIMLANE','ELSE','ENDIF'):
                continue
            if t['id'] in self.elements and self.elements[t['id']]['type'] not in ('note',):
                return t['id']
        return None

    def _first_after_token(self, token_id):
        idx = None
        for i,tok in enumerate(self.ast):
            if tok['id']==token_id:
                idx = i
                break
        if idx is None:
            return None
        for j in range(idx+1, len(self.ast)):
            cand = self.ast[j]
            if cand['type'] in ('SWIMLANE','ELSE'):
                continue
            if cand['id'] in self.elements and self.elements[cand['id']]['type'] not in ('note',):
                return cand['id']
        return None

    def _previous_executable(self, token_id):
        idx = None
        for i, tok in enumerate(self.ast):
            if tok['id'] == token_id:
                idx = i
                break
        if idx is None:
            return None
        for j in range(idx - 1, -1, -1):
            cand = self.ast[j]
            if cand['type'] in ('SWIMLANE', 'ELSE'):
                continue
            elem = self.elements.get(cand['id'])
            if elem and elem['type'] not in ('note', 'else_marker'):
                return cand['id']
        return None

    def _first_between(self, start_id, end_id):
        started=False
        for tok in self.ast:
            if tok['id']==start_id:
                started=True
                continue
            if tok['id']==end_id:
                break
            if started and tok['id'] in self.elements:
                et = self.elements[tok['id']]['type']
                if et not in ('note',):
                    return tok['id']
        return None

    # ---------------- VALIDATION / REPAIR (minimal) ----------------
    def _compute_topology_metadata(self):
        """
        (3) & (4) Zlicza incoming/outgoing i taguje decision_end:
          - incoming_count / outgoing_count
          - merge_candidate (incoming>=2)
          - redundant_merge (incoming==1)
        """
        incoming = {}
        outgoing = {}
        for c in self.connections:
            outgoing[c['source_id']] = outgoing.get(c['source_id'], 0) + 1
            incoming[c['target_id']] = incoming.get(c['target_id'], 0) + 1
        for eid, elem in self.elements.items():
            ic = incoming.get(eid, 0)
            oc = outgoing.get(eid, 0)
            elem['incoming_count'] = ic
            elem['outgoing_count'] = oc
            # role podstawowa
            if elem['type'] == 'start':
                elem['role'] = 'initial'
            elif elem['type'] == 'end':
                elem['role'] = 'final'
            elif elem['type'] == 'decision':
                elem['role'] = 'decision'
            elif elem['type'] in ('repeat_start', 'loop_start'):
                elem['role'] = 'loop_entry'
            elif elem['type'] in ('repeat_end', 'loop_end'):
                elem['role'] = 'loop_test'
            elif elem['type'] == 'decision_end':
                if ic >= 2:
                    elem['merge_candidate'] = True
                    elem['role'] = 'merge_candidate'
                elif ic == 1:
                    elem['redundant_merge'] = True
                    elem['role'] = 'redundant'
                else:
                    elem['role'] = 'decision_end'
            elif elem['type'] == 'else_marker':
                elem['role'] = 'else_marker'
            elif elem['type'] == 'activity':
                elem['role'] = 'action'
            else:
                elem['role'] = elem['type']

    def _validate_and_repair(self):
        # Usuń krawędzie wychodzące z end oraz (2) krawędzie z/do note
        cleaned = []
        for c in self.connections:
            src_t = self.elements.get(c['source_id'], {}).get('type')
            tgt_t = self.elements.get(c['target_id'], {}).get('type')
            if src_t == 'end':
                continue
            if src_t == 'note' or tgt_t == 'note':
                continue
            cleaned.append(c)
        self.connections = cleaned
        # (opcjonalnie) Można tu logować problematyczne decision_end bez outgoing,
        # ale faktyczna transformacja / scalanie nastąpi w generatorze XMI.
        if self.debug.get('parsing'):
            merges = [e for e in self.elements.values() if e.get('merge_candidate')]
            red = [e for e in self.elements.values() if e.get('redundant_merge')]
            log_debug(f"Merge candidates: {len(merges)}, redundant decision_end: {len(red)}")

    def _normalize_guards(self):
        for c in self.connections:
            raw = (c.get('label') or '').strip('[]').strip()
            low = raw.lower()
            norm = raw
            if low in ('true','yes','tak'):
                norm = 'tak'
            elif low in ('false','no','nie'):
                norm = 'nie'
            elif ' is true' in low:
                norm = 'tak'
            elif ' is false' in low:
                norm = 'nie'
            c['guard_raw'] = raw
            c['guard_norm'] = norm

    def _inline_else_markers(self):
        """
        (5) Usuwa węzły else_marker:
         - decision --(guard 'nie')--> else_marker --( )--> X
           staje się: decision --('nie')--> X
        Jeśli gałąź else pusta i marker prowadzi do decision_end, decyzja łączy się bezpośrednio.
        """
        # Zbuduj indeks krawędzi
        if not any(e['type']=='else_marker' for e in self.elements.values()):
            return
        to_remove_nodes = []
        new_edges = []
        # indeksy
        incoming_map = {}
        outgoing_map = {}
        for c in self.connections:
            incoming_map.setdefault(c['target_id'], []).append(c)
            outgoing_map.setdefault(c['source_id'], []).append(c)

        for eid, elem in list(self.elements.items()):
            if elem['type'] != 'else_marker':
                continue
            src_edges = incoming_map.get(eid, [])
            out_edges = outgoing_map.get(eid, [])
            # oczekujemy jednego źródła (decision)
            guard_label = None
            decision_id = None
            for se in src_edges:
                decision_id = se['source_id']
                guard_label = se.get('label') or elem.get('else_label','nie')
            if decision_id:
                for oe in out_edges:
                    tgt = oe['target_id']
                    # przenieś guard na krawędź decision->tgt (zachowaj etype control_flow)
                    self._add_edge(decision_id, tgt, guard_label)
            # jeśli brak out_edges (pusta gałąź else) – połącz decyzję z ewentualnym merge (decision_end)
            if decision_id and not out_edges:
                # poszukaj decision_end w dół strumienia (jeśli był)
                for se in src_edges:
                    # nic do zrobienia – w _decision_edges była już krawędź decision->decision_end
                    pass
            # oznacz do usunięcia
            to_remove_nodes.append(eid)

        if not to_remove_nodes:
            return
        # Usuń krawędzie z/ do else_marker
        self.connections = [c for c in self.connections if c['source_id'] not in to_remove_nodes and c['target_id'] not in to_remove_nodes]
        # Usuń elementy
        for nid in to_remove_nodes:
            self.elements.pop(nid, None)

    def _consolidate_final_nodes(self):
        """
        Konsolidacja final nodes:
          - Nie scala finali o różnych sygnaturach (poprzedzający tekst/kolor).
          - Scala tylko duplikaty finali o tej samej sygnaturze (więcej niż jeden).
          - Zawsze usuwa outgoing z final (bezpiecznik).
        Sygnatura finala = (poprzednia_akcja.text, poprzednia_akcja.color)
        """
        finals = [eid for eid, e in self.elements.items() if e['type'] == 'end']
        if not finals:
            return

        # zbuduj mapę poprzedników pojedynczych (tylko jeśli dokładnie 1 incoming)
        incoming_edges_by_target = {}
        for c in self.connections:
            incoming_edges_by_target.setdefault(c['target_id'], []).append(c)

        def final_signature(fid):
            inc = incoming_edges_by_target.get(fid, [])
            if len(inc) != 1:
                return None  # brak jednoznacznej sygnatury -> nie scalać z innymi
            src_elem = self.elements.get(inc[0]['source_id'])
            if not src_elem:
                return None
            return (src_elem.get('text'), src_elem.get('color'))

        groups = {}
        for fid in finals:
            sig = final_signature(fid)
            groups.setdefault(sig, []).append(fid)

        to_remove = []
        # scalaj tylko grupy z identyczną sygnaturą mające >1 final
        for sig, fids in groups.items():
            if sig is None or len(fids) <= 1:
                continue
            canonical = fids[0]
            for extra in fids[1:]:
                # przepnij pojedynczy incoming na canonical (incoming mamy pewny bo sig != None)
                inc_edge = incoming_edges_by_target.get(extra, [])
                if len(inc_edge) == 1:
                    src = inc_edge[0]['source_id']
                    self._add_edge(src, canonical, inc_edge[0].get('label', ''))
                to_remove.append(extra)

        if to_remove:
            self.connections = [
                c for c in self.connections
                if c['target_id'] not in to_remove and c['source_id'] not in to_remove
            ]
            for rid in to_remove:
                self.elements.pop(rid, None)

        # Usuń outgoing z pozostałych final (bezpiecznik UML)
        remaining_finals = [eid for eid, e in self.elements.items() if e['type'] == 'end']
        if remaining_finals:
            self.connections = [c for c in self.connections if c['source_id'] not in remaining_finals]

        if self.debug.get('parsing') and to_remove:
            log_debug(f"Konsolidacja final: scalono {len(to_remove)} duplikatów (grup wg sygnatur).")

    # ---------------- OUTPUT ----------------
    def _prepare_result(self) -> Dict[str, Any]:
        # else_marker już wycięte – upewnij się że nie trafiają do flow
        flow = [e for e in self.elements.values() if e['type'] != 'else_marker']
        logical_connections = self.connections
        for e in flow:
            sl = e.get('swimlane')
            if sl and e['type'] in ('activity','decision','repeat_start','repeat_end','loop_start','loop_end'):
                self.swimlanes.setdefault(sl, {'activities': []})['activities'].append(e)
        return {
            'title': self.title,
            'flow': flow,
            'elements': {e['id']: e for e in flow},
            'logical_connections': logical_connections,
            'swimlanes': self.swimlanes,
            'feature_flags': {
                'else_inlined': True,
                'final_consolidation': True,
                'loop_condition_split': True
            },
            'stats': {
                'total_elements': len(flow),
                'total_connections': len(logical_connections),
                'total_swimlanes': len(self.swimlanes)
            }
        }

# ------------- CLI -------------
if __name__ == '__main__':
    import argparse
    setup_logger('improved_plantuml_activity_parser.log')
    ap = argparse.ArgumentParser()
    ap.add_argument('input', nargs='?', default='Diagram_aktywności_z_aktorami.puml')
    ap.add_argument('-o','--output')
    ap.add_argument('-d','--debug', action='store_true')
    args = ap.parse_args()

    with open(args.input,'r',encoding='utf-8') as f:
        code = f.read()

    parser = ImprovedPlantUMLActivityParser(code, {'parsing':args.debug,'decisions':args.debug})
    result = parser.parse()
    out = args.output or f"activity_diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out,'w',encoding='utf-8') as f:
        json.dump(result,f,indent=2,ensure_ascii=False)
    log_info(f"OK: elements={result['stats']['total_elements']} edges={result['stats']['total_connections']}")
