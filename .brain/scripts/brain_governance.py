"""Brain/skill checks; PyYAML is required for full frontmatter validation. No operational helper is executed."""
from pathlib import Path
import argparse,ast,json,re,sys

MINOR={'a','an','and','as','at','but','by','for','from','in','into','of','on','or','per','the','to','via','vs','with','without'}
SPECIAL={'i18n','a11y','scikit-learn','gVisor','macOS','iOS','Node.js','JavaScript','TypeScript','PyTorch','NumPy','AutoML','pytest','pandas','uv','npm','pnpm'}

def valid_skill_name(name):
    return len(name)<=64 and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) is not None

def note_title(title):
    words=title.strip().split()
    def word(value,index):
        if value in SPECIAL or value.isupper():return value
        if 0<index<len(words)-1 and value.casefold() in MINOR:return value.casefold()
        return value[:1].upper()+value[1:]
    return ' '.join(word(w,i) for i,w in enumerate(words))

def validate_skill(root):
    root=Path(root);issues=[];manifest=root/'SKILL.md'
    if not manifest.is_file():return ['Missing SKILL.md']
    text=manifest.read_text(encoding='utf-8-sig')
    match=re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)',text,re.S)
    if not match:return ['Missing YAML frontmatter delimiters']
    front=match[1]
    try:
        import yaml
        metadata=yaml.safe_load(front)
        if not isinstance(metadata,dict):return ['Frontmatter must be a YAML mapping']
        if not isinstance(metadata.get('description'),str) or not metadata['description'].strip():issues.append('Description must be a nonempty YAML string')
        if not isinstance(metadata.get('name'),str):issues.append('Name must be a YAML string')
        unexpected=set(metadata)-{'name','description','license','allowed-tools','metadata'}
        if unexpected:issues.append('Unsupported frontmatter fields: '+', '.join(sorted(unexpected)))
        description_value=metadata.get('description','')
        if isinstance(description_value,str) and (len(description_value)>1024 or '<' in description_value or '>' in description_value):issues.append('Description must be at most 1024 characters and contain no angle brackets')
    except ImportError:return ['Install PyYAML for full frontmatter validation: python -m pip install PyYAML']
    except yaml.YAMLError:return ['Invalid YAML frontmatter']
    name=re.search(r'(?m)^name:[ \t]*[\"\']?([^\r\n\"\']+)',front)
    name=name[1].strip() if name else ''
    if not valid_skill_name(name) or name!=root.name:issues.append('Skill name must match its lowercase kebab-case directory (maximum 64 characters)')
    description=re.search(r'(?m)^description:[ \t]*(.+)',front)
    if not description or not description[1].strip(' \"\''):issues.append('Missing nonempty description')
    if not text[match.end():].strip():issues.append('Missing workflow body')
    if re.search(r'\[(?:TODO|INSERT|REPLACE)[^\]]*\]',text,re.I):issues.append('Unfinished scaffold placeholder')
    scripts=[p for p in (root/'scripts').rglob('*') if p.is_file() and p.suffix in {'.py','.ps1','.sh','.js','.mjs','.ts'}] if (root/'scripts').is_dir() else []
    if not scripts:issues.append('Missing executable script in scripts/')
    for script in scripts:
        if not script.resolve().is_relative_to(root.resolve()):issues.append('Script escapes skill directory: '+script.name);continue
        if not script.stat().st_size:issues.append('Empty script: '+script.name)
        if script.suffix=='.py':
            try:ast.parse(script.read_text(encoding='utf-8-sig'),filename=str(script))
            except (SyntaxError,UnicodeError) as error:issues.append('Python syntax error: '+script.name+': '+str(error))
    return issues

def create_skill(parent,name,description,body):
    if not valid_skill_name(name):raise ValueError('Invalid skill name')
    if not description.strip() or not body.strip():raise ValueError('Description and workflow are required')
    if len(description)>1024 or '<' in description or '>' in description:raise ValueError('Description must be at most 1024 characters and contain no angle brackets')
    root=Path(parent)/name
    root.mkdir(parents=True,exist_ok=False)
    (root/'scripts').mkdir()
    (root/'SKILL.md').write_text('---\nname: '+name+'\ndescription: '+json.dumps(description,ensure_ascii=False)+'\n---\n\n# '+note_title(name.replace('-',' '))+'\n\n'+body.strip()+'\n\n## Validation\n\nRun `python scripts/validate_skill.py` from this skill directory. This checks structure and Python syntax, not workflow correctness. Test operational helpers against representative inputs before using them.\n',encoding='utf-8',newline='\n')
    # Self-contained validator travels with the skill; no user-specific installation path.
    (root/'scripts/validate_skill.py').write_bytes(Path(__file__).read_bytes())
    issues=validate_skill(root)
    if issues:raise ValueError('; '.join(issues))
    return root

def empty_content_dirs(root):
    root=Path(root)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir() and not any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(root).parts) and not any(p.iterdir()))

def validate_names(root):
    root=Path(root);issues=[]
    for note in root.glob('*.md'):
        if note.name in {'AGENTS.md','AGENTS.override.md','README.md','CLAUDE.md','SKILL.md'}:continue
        expected=note_title(note.stem)
        if expected!=note.stem:issues.append(note.name+' -> '+expected+'.md')
    for skill in root.glob('.agents/skills/*'):
        if skill.is_dir() and (skill/'SKILL.md').exists():issues.extend(str(skill.relative_to(root))+': '+e for e in validate_skill(skill))
    return issues

def route_config(root):
    path=Path(root)/'.brain.json'
    return json.loads(path.read_text(encoding='utf-8-sig'))

def initialize_project(root,developer):
    root=Path(root).resolve();developer=Path(developer).expanduser().resolve()
    if not (developer/'Knowledge MOC.md').is_file():raise ValueError('Developer entrypoint is missing')
    if (root/'.brain.json').exists():raise FileExistsError('Existing route must be maintained explicitly')
    brain=root/'.brain/vault'
    if brain.exists():raise FileExistsError('Existing project brain must not be overwritten')
    brain.mkdir(parents=True)
    (brain/'Project MOC.md').write_text('# Project MOC\n\nRead [[Project Context]] before work.\n\n#architecture #tooling #generated_by_ai\n',encoding='utf-8')
    (brain/'Project Context.md').write_text('# Project Context\n\nInitial project brain. Architecture and operational commands are not verified yet. Read current source, record evidence and update this note during work.\n\nRelated: [[Project MOC]]\n\n#architecture #tooling #generated_by_ai\n',encoding='utf-8')
    config={'schema_version':1,'developer_vault':str(developer),'project_vault':'.brain/vault','project_entrypoint':'Project MOC.md'}
    (root/'.brain.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    return config

def session_context(root,query=''):
    issues=validate_route(root)
    if issues:raise ValueError('; '.join(issues))
    config=route_config(root);result=[]
    for key in ('developer_vault','project_vault'):
        path=Path(config[key]).expanduser()
        if not path.is_absolute():path=Path(root)/path
        entry=path/('Knowledge MOC.md' if key=='developer_vault' else config.get('project_entrypoint',path.name+' MOC.md'))
        result.append({'role':key,'path':str(entry),'content':entry.read_text(encoding='utf-8-sig')})
        if query:
            matches=[p for p in path.glob('*.md') if p!=entry and query.casefold() in p.read_text(encoding='utf-8-sig').casefold()]
            result.append({'role':key,'query':query,'matching_notes':[str(p) for p in matches]})
    return result

def validate_route(root):
    try:config=route_config(root)
    except (OSError,ValueError):return ['Missing or invalid .brain.json']
    issues=[]
    for key in ('developer_vault','project_vault'):
        value=config.get(key)
        if not value:issues.append('Missing '+key);continue
        if 'personal-notes' in str(value).casefold():issues.append('Personal notes cannot be a managed brain');continue
        path=Path(value).expanduser()
        if not path.is_absolute():path=Path(root)/path
        if not path.is_dir():issues.append('Missing vault: '+str(path));continue
        entry='Knowledge MOC.md' if key=='developer_vault' else config.get('project_entrypoint',path.name+' MOC.md')
        if not (path/entry).is_file():issues.append('Missing entrypoint: '+str(path/entry))
    return issues

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',nargs='?',choices=['skill','names','route','empty','create','init-project','start'],default='skill')
    parser.add_argument('path',nargs='?',type=Path)
    parser.add_argument('--name');parser.add_argument('--description');parser.add_argument('--body-file',type=Path)
    parser.add_argument('--developer-vault',default='~/Documents/Codex/Vaults/Developer');parser.add_argument('--query',default='')
    args=parser.parse_args();path=args.path or Path(__file__).resolve().parents[1]
    if args.mode=='init-project':print(json.dumps(initialize_project(path,args.developer_vault)));return
    if args.mode=='start':print(json.dumps(session_context(path,args.query),ensure_ascii=True,indent=2));return
    if args.mode=='create':
        if not (args.name and args.description and args.body_file):parser.error('create requires --name, --description and --body-file')
        print(create_skill(path,args.name,args.description,args.body_file.read_text(encoding='utf-8')));return
    check={'skill':validate_skill,'names':validate_names,'route':validate_route,'empty':empty_content_dirs}[args.mode]
    issues=check(path);print(json.dumps({'check':args.mode,'issues':issues},ensure_ascii=True,indent=2));sys.exit(bool(issues))

if __name__=='__main__':main()
