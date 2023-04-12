*** Settings ***
Library    Process
Library    OperatingSystem
Library    SSHLibrary
Library    String
Suite Setup    Suite Setup
Suite Teardown    Suite Teardown
Test Setup    Test Setup
#Test Teardown    Test Teardown

*** Variables ***
${INVENTORY}    inventory
${INVENTORY_ABSOLUE_PATH}    ac_tests/${INVENTORY}
${PLAYBOOKS_FOLDER}    playbooks/instances
${PLAYBOOKS_CREATE_FOLDER}    ${PLAYBOOKS_FOLDER}/create_modify
${PLAYBOOKS_STATE_FOLDER}    ${PLAYBOOKS_FOLDER}/state
${PLAYBOOKS_ADMIN_STATE_FOLDER}    ${PLAYBOOKS_FOLDER}/admin_state
${PLAYBOOK_CREATE}    ${PLAYBOOKS_CREATE_FOLDER}/create_instance.yml
${PLAYBOOK_CREATE_NO_NICS}    ${PLAYBOOKS_CREATE_FOLDER}/create_no_nics_instance.yml
${PLAYBOOK_MODIFY}    ${PLAYBOOKS_CREATE_FOLDER}/modify_instance.yml
${PLAYBOOK_CREATE_MULTI}    ${PLAYBOOKS_CREATE_FOLDER}/create_multi_instances.yml
*** Test Cases ***
Create Instance
    Run Ansible Playbook    ${PLAYBOOK_CREATE}    tag=create    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}


Create Multi Instance
    Run Ansible Playbook    ${PLAYBOOK_CREATE_MULTI}    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}

Modify Instance
    Run Ansible Playbook    ${PLAYBOOK_MODIFY}    tag=create    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}
    Run Ansible Playbook    ${PLAYBOOK_MODIFY}    tag=modify    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}

Create No Nics Instance
    Run Ansible Playbook    ${PLAYBOOK_CREATE_NO_NICS}    tag=create    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}
    #Run Ansible Playbook    ${PLAYBOOK_CREATE_NO_NICS}    tag=modify    inventory=${INVENTORY}
    ${stdout}=    Execute Command    sudo gnt-instance info --all
    Log    ${stdout}


Remove VM
    Run Ansible Playbook    ${PLAYBOOKS_STATE_FOLDER}/present.yml    inventory=${INVENTORY}
    Should Instance Exist    instance_state
    Run Ansible Playbook    ${PLAYBOOKS_STATE_FOLDER}/absent.yml    inventory=${INVENTORY}
    Should Instance Not Exist    instance_state


Can stop, start and restart VM
    Run Ansible Playbook    ${PLAYBOOKS_ADMIN_STATE_FOLDER}/instance.yml    inventory=${INVENTORY}
    Check instance admin state    instance_admin_state    down
    Run Ansible Playbook    ${PLAYBOOKS_ADMIN_STATE_FOLDER}/restart.yml    inventory=${INVENTORY}
    Check instance admin state    instance_admin_state    up
    Run Ansible Playbook    ${PLAYBOOKS_ADMIN_STATE_FOLDER}/stop.yml    inventory=${INVENTORY}
    Check instance admin state    instance_admin_state    down
    Run Ansible Playbook    ${PLAYBOOKS_ADMIN_STATE_FOLDER}/start.yml    inventory=${INVENTORY}
    Check instance admin state    instance_admin_state    up


*** Keywords ***
Suite Setup
    Run Vagrant And Get VM IP    %{DEBIAN_VERSION}
    Create inventory

Suite Teardown
    Remove inventory
    #Run Process    vagrant destroy --force    shell=True    cwd=infra
    Run Process    vagrant halt --force   shell=True    cwd=infra

Test Setup
    Open Connection    ${IP_VM}
    Login    vagrant     vagrant
    Clean Ganeti
    Create Ganeti Cluster    %{DEBIAN_VERSION}

Test Teardown
    Clean Ganeti
    Close All Connections

Create Ganeti Cluster
    [Arguments]    ${debian_version}=stretch
    ${option}=    Set Variable If    "${debian_version}" == "stretch"    ${EMPTY}    --default-iallocator-params\='-no-capacity-checks'
    ${stdout}    ${stderr}    ${rc}=    Execute Command    sudo gnt-cluster init --master-netdev=br_gnt --enabled-hypervisors=fake --enabled-disk-templates=file ${option} cluster-test    return_stdout=True    return_stderr=True    return_rc=True
    Log    ${stdout}
    Should Be Equal as Integers   0    ${rc}    msg=Cannot create ClusterVM\n${stdout}\n${stderr}

Clean Ganeti
    Execute Command    sudo gnt-instance stop --timeout\=0 --all
    #Execute Command    sudo gnt-cluster destroy --yes-do-it
    Execute Command    sudo rm -rf /var/lib/ganeti/*
    Execute Command    /etc/init.d/ganeti restart

Create inventory
    Create File    ${INVENTORY_ABSOLUE_PATH}    [all]\ntest ansible_host=${IP_VM} ansible_user=vagrant ansible_ssh_pass=vagrant
    ${file}=    OperatingSystem.Get File    ${INVENTORY_ABSOLUE_PATH}
    Log    ${file}

Remove inventory
    Remove File    ${INVENTORY_ABSOLUE_PATH}

Run Vagrant And Get VM IP
    [Arguments]    ${debian_version}=stretch
    #${result}=    Run Process    vagrant plugin install vagrant-libvirt    shell=True    cwd=infra
    #Log    ${result.stdout}
    #Should Be Equal as Integers   0    ${result.rc}    msg=Impossible to install libvirt provider\n${result.stderr}
    ${result}=    Run Process    vagrant up --provider\=libvirt --no-provision ${debian_version}    shell=True    cwd=infra
    Log    ${result.stdout}
    Should Be Equal as Integers   0    ${result.rc}    msg=Cannot create VM\n${result.stderr}
    ${result}=    Run Process    vagrant ssh --command "hostname -i" ${debian_version}    shell=True    cwd=infra
    Log    ${result.stdout}
    Should Be Equal as Integers   0    ${result.rc}    msg=Cannot get VM IP\n${result.stderr}
    ${IP_VM}=    Strip String    ${result.stdout}
    Log    "${IP_VM}"
    Should Not Be Empty    ${IP_VM}    msg=Cannot get VM IP\n${result.stderr}
    Set Suite Variable    ${IP_VM}

Run Ansible Playbook
    [Arguments]    ${playbook}    ${inventory}=${INVENTORY}    ${tag}=${EMPTY}
    ${tag_option}=    Set Variable If    "${tag}"=="${EMPTY}"    ${EMPTY}    -t ${tag}
    ${result}=    Run Process    python3 \$(which ansible-playbook) -vvv ${tag_option} -i ${inventory} ${playbook}    shell=True    cwd=ac_tests
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    0    ${result.rc}    msg=Ansible Playbook have error\n${result.stdout}\n${result.stderr}

Check instance admin state
    [Arguments]    ${instance}    ${state}
    ${stdout}=    Execute Command    sudo gnt-instance info ${instance}
    Log    ${stdout}
    Should Match Regexp    ${stdout}    State: configured to be ${state}, actual state is ${state}

Should Instance Exist
    [Arguments]    ${instance}
    ${stdout}=    Execute Command    sudo gnt-instance info ${instance}
    Log    ${stdout}
    Should Match Regexp    ${stdout}    Instance name: ${instance}

Should Instance Not Exist
    [Arguments]    ${instance}
    ${rc}=    Execute Command    sudo gnt-instance info ${instance}    return_stdout=False    return_rc=True
    Log    ${rc}
    Should Be Equal As Integers    1    ${rc}