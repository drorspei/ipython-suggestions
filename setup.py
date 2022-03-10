from setuptools import setup


if __name__ == "__main__":
    setup(
        name="ipython-suggestions",
        version="1.0.0",
        description="Get suggestions on misspelled names, and do system wide symbol searching.",
        long_description=open("README.md").read(),
        long_description_content_type='text/markdown',
        author="Dror Speiser",
        url="https://github.com/drorspei/ipython-suggestions",
        license="MIT",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: IPython",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
        ],
        py_modules=["ipython_suggestions", "super_greedy_complete"],
        python_requires=">=2.7.10",
        install_requires=["ipython>=4.0", 'future;python_version<"3"'],
    )
