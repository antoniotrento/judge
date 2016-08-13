import os
import traceback
from distutils.spawn import find_executable
from importlib import import_module

import yaml
import yaml.representer

from dmoj import judgeenv
from dmoj.executors import executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style

TEST_ON_TRAVIS = ['ADA', 'AWK', 'BF', 'C', 'CPP03', 'CPP11', 'CPP14', 'CLANG', 'CLANGX',
                  'COFFEE', 'GO', 'HASK', 'JAVA7', 'JAVA8', 'MONOCS',
                  'GAS32', 'GAS64', 'NASM', 'NASM64',
                  'PERL', 'PHP', 'PY2', 'PY3', 'PYPY', 'PYPY3', 'RUBY19', 'SCALA', 'TEXT']
OVERRIDES = {
    'PY2': {'python': '/usr/bin/python'},
    'RUBY19': {'ruby19': find_executable('ruby')},
    'PYPY': {'pypy_home': '/opt/python/pypy-2.5.0'},
    'PYPY3': {'pypy3_home': '/opt/python/pypy3-2.4.0'},
}


def get_dirs(dir):
    try:
        return [item for item in os.listdir(dir) if os.path.isdir(os.path.join(dir, item))]
    except OSError:
        return []


def main():
    result = {}

    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {
        'PHP': ['/etc/php5/', '/etc/terminfo/', '/etc/protocols$'],
        'RUBY19': ['/home/travis/.rvm/rubies/'],
    }

    failed = False

    print 'Available JVMs:'
    for jvm in get_dirs('/usr/lib/jvm/'):
        print '  -', jvm
    print

    print 'Available Pythons:'
    for python in get_dirs('/opt/python'):
        print '  -', python
    print

    print 'Available Rubies:'
    for ruby in get_dirs(os.path.expanduser('~/.rvm/rubies')):
        print '  -', ruby
    print

    print 'Testing executors...'

    for name in TEST_ON_TRAVIS:
        executor = import_module('dmoj.executors.' + name)

        print ansi_style('%-34s%s' % ('Testing #ansi[%s](|underline):' % name, '')),

        if not hasattr(executor, 'Executor'):
            failed = True
            print ansi_style('#ansi[Does not export](red|bold) #ansi[Executor](red|underline)')
            continue

        if not hasattr(executor.Executor, 'autoconfig'):
            print ansi_style('#ansi[Could not autoconfig](magenta|bold)')
            continue

        try:
            if name in OVERRIDES:
                print ansi_style('#ansi[(manual config)](yellow)'),
                data = executor.Executor.autoconfig_run_test(OVERRIDES[name])
            else:
                data = executor.Executor.autoconfig()
            config = data[0]
            success = data[1]
            feedback = data[2]
            errors = '' if len(data) < 4 else data[3]
        except Exception:
            failed = True
            print ansi_style('#ansi[Autoconfig broken](red|bold)')
            traceback.print_exc()
        else:
            print ansi_style(['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] %
                             (feedback or ['Failed', 'Success'][success]))

            if success:
                result.update(config)
                executor.Executor.runtime_dict = config
                executors[name] = executor
            else:
                if config:
                    print '  Attempted:'
                    print '   ', yaml.dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4)

                if errors:
                    print '  Errors:'
                    print '   ', errors.replace('\n', '\n' + ' ' * 4)
                failed = True

    print
    print ansi_style('#ansi[Configuration result](green|bold|underline):')
    print yaml.dump({'runtime': result}, default_flow_style=False).rstrip()
    print
    print
    print 'Running test cases...'
    judgeenv.problem_dirs = [os.path.join(os.path.dirname(__file__), 'testsuite')]
    tester = Tester()
    fails = tester.test_all()
    print
    print 'Test complete'
    if fails:
        print ansi_style('#ansi[A total of %d case(s) failed](red|bold).') % fails
    else:
        print ansi_style('#ansi[All cases passed.](green|bold)')
    failed |= fails != 0
    raise SystemExit(int(failed))


if __name__ == '__main__':
    main()
