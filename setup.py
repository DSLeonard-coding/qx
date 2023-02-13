import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

exec(open('qx/version.py').read())

setuptools.setup(
    name='qx',
    version=__version__,
    author='Doug Leonard',
    author_email='dleonard.dev@gmail.com',
    description='a perl-like qx(), ie backticks. Runs a shell command and returns a CompletedProcess',
    long_description_content_type="text/markdown",
    url='https://gitlab.com/douglas.s.leonard/qx',
    project_urls = {
        "Bug Tracker": "https://gitlab.com/douglas.s.leonard/qx"
    },
    license='MIT',
    packages=['qx'],
    package_data={'qx': ['py.typed']},
    install_requires=[],
)
