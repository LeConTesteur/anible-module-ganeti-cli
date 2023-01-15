*** Settings ***
Library    Process
Library    OperatingSystem
Library    SSHLibrary
Library    String
Suite Setup    Suite Setup
Suite Teardown    Suite Teardown
Test Setup    Test Setup
Test Teardown    Test Teardown

*** Variables ***
${INVENTORY}    inventory
${INVENTORY_ABSOLUE_PATH}    ac_tests/${INVENTORY}
${PLAYBOOK_INSTANCE}    pk_instance.yml

*** Test Cases ***
Test
    ${result}=    Run Process    ansible-playbook -i ${INVENTORY} ${PLAYBOOK_INSTANCE}    shell=True    cwd=ac_tests
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    0    ${result.rc}    msg=Ansible Playbook have error\n${result.stderr}
    ${test_recap}=    Get Lines Matching Regexp    ${result.stdout}    test\\s+[:]\\s+ok    partial_match=${True}
    ${states}=    Should Match Regexp    ${test_recap}    (\\w+\=\\w+)
    Log    ${states}


*** Keywords ***
Suite Setup
    Run Process    vagrant up --provider\=libvirt stretch64    shell=True    cwd=infra
    ${result}=    Run Process    vagrant ssh --command "hostname -I" stretch64    shell=True    cwd=infra
    ${IP_VM}=    Strip String    ${result.stdout}
    Log    "${IP_VM}"
    Set Suite Variable    ${IP_VM}
    Create inventory

Suite Teardown
    Remove inventory
    #Run Process    vagrant destroy --force    shell=True    cwd=infra
    Run Process    vagrant halt --force   shell=True    cwd=infra

Test Setup
    Open Connection    ${IP_VM}
    Login    vagrant     vagrant
    Clean Ganeti
    Create Ganeti Cluster

Test Teardown
    Clean Ganeti
    Close All Connections

Create Ganeti Cluster
    Execute Command    sudo gnt-cluster init

Clean Ganeti
    Execute Command    sudo gnt-instance stop --timeout\=0 --all
    Execute Command    sudo gnt-cluster destroy --yes-do-it

Create inventory
    Create File    ${INVENTORY_ABSOLUE_PATH}    [all]\ntest ansible_host=${IP_VM} ansible_user=vagrant ansible_ssh_pass=vagrant
    ${file}=    OperatingSystem.Get File    ${INVENTORY_ABSOLUE_PATH}
    Log    ${file}

Remove inventory
    Remove File    ${INVENTORY_ABSOLUE_PATH}