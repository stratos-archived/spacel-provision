dockerBuild {
    name = 'pwagner/spacel-provision'
    testCommand = 'make composetest'
    reports = [
        tests: '**/build/nosetests.xml',
        tasks: '**/*.py'
    ]
}

