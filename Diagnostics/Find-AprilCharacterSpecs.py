from pathlib import Path
import importlib.util
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tor',here/'extract-tor-paths.py')
tor=importlib.util.module_from_spec(spec);spec.loader.exec_module(tor)
names=['petmouse','acklay','colicoid','klorslugboss','rancorboss','manta']
paths=[f'{prefix}/art/dynamic/spec/{name}.dat' for name in names for prefix in ('','/resources')]
wanted={tor.tor_hash(path):path for path in paths}
for archive in (here.parent/'Assets2012April').glob('*.tor'):
    with archive.open('rb') as f:
        for entry in tor.archive_entries(f):
            if entry[4] in wanted:
                print(archive.name,wanted[entry[4]],entry[3])
