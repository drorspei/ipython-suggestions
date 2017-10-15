from setuptools import setup
import versioneer


if __name__ == "__main__":
    setup(
        name="ipython-suggestions",
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description="Get suggestions on misspelled names, and do system wide symbol searching.",
        long_description=open("README.rst").read(),
        author="Dror Speiser",
        url="https://github.com/drorspei/ipython-suggestions",
        license="MIT",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: IPython",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
        ],
        py_modules=["ipython_suggestions"],
        python_requires=">=2.7.10",
        install_requires=["ipython>=4.0", 'future;python_version<"3"'],
    )
