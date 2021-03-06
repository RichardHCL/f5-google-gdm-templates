# Copyright 2018 F5 Networks All rights reserved.
#
# Version v1.5.1

"""Creates BIG-IP"""
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'
def GenerateConfig(context):
  ALLOWUSAGEANALYTICS = context.properties['allowUsageAnalytics']
  if ALLOWUSAGEANALYTICS == "yes":
      CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;\n'
      SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-existing-stack-byol-2nic-bigip.py,templateVersion:v1.5.1,licenseType:byol"'
  else:
      CUSTHASH = ''
      SENDANALYTICS = ''
  resources = [{
      'name': 'bigip1-' + context.env['deployment'],
      'type': 'compute.v1.instance',
      'properties': {
          'zone': context.properties['availabilityZone1'],
          'canIpForward': True,
          'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/zones/',
                                  context.properties['availabilityZone1'], '/machineTypes/',
                                  context.properties['instanceType']]),
          'serviceAccounts': [{
              'email': context.properties['serviceAccount'],
              'scopes': ['https://www.googleapis.com/auth/compute.readonly']
          }],
          'disks': [{
              'deviceName': 'boot',
              'type': 'PERSISTENT',
              'boot': True,
              'autoDelete': True,
              'initializeParams': {
                  'sourceImage': ''.join([COMPUTE_URL_BASE, 'projects/f5-7626-networks-public',
                                          '/global/images/',
                                          context.properties['imageName'],
                                         ])
              }
          }],
          'networkInterfaces': [{
              'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/global/networks/',
                                  context.properties['mgmtNetwork']]),
              'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/regions/',
                                  context.properties['region'], '/subnetworks/',
                                  context.properties['mgmtSubnet']]),
              'accessConfigs': [{
                  'name': 'Management NAT',
                  'type': 'ONE_TO_ONE_NAT'
              }],
          },
          {
              'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/global/networks/',
                                  context.properties['network1']]),
              'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/regions/',
                                  context.properties['region'], '/subnetworks/',
                                  context.properties['subnet1']]),
              'accessConfigs': [{
                  'name': 'External NAT',
                  'type': 'ONE_TO_ONE_NAT'
              }],
          }],
          'metadata': {
              'items': [{
                  'key': 'startup-script',
                  'value': (''.join(['#!/bin/bash\n',
                                    'if [ -f /config/startupFinished ]; then\n',
                                    '    exit\n',
                                    'fi\n',
                                    'mkdir -p /config/cloud/gce\n',
                                    'cat <<\'EOF\' > /config/installCloudLibs.sh\n',
                                    '#!/bin/bash\n',
                                    'echo about to execute\n',
                                    'checks=0\n',
                                    'while [ $checks -lt 120 ]; do echo checking mcpd\n',
                                    '    tmsh -a show sys mcp-state field-fmt | grep -q running\n',
                                    '    if [ $? == 0 ]; then\n',
                                    '        echo mcpd ready\n',
                                    '        break\n',
                                    '    fi\n',
                                    '    echo mcpd not ready yet\n',
                                    '    let checks=checks+1\n',
                                    '    sleep 10\n',
                                    'done\n',
                                    'echo loading verifyHash script\n',
                                    'if ! tmsh load sys config merge file /config/verifyHash; then\n',
                                    '    echo cannot validate signature of /config/verifyHash\n',
                                    '    exit\n',
                                    'fi\n',
                                    'echo loaded verifyHash\n',
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/config/cloud/f5.service_discovery.tmpl\")\n',
                                    'for fileToVerify in \"${filesToVerify[@]}\"\n',
                                    'do\n',
                                    '    echo verifying \"$fileToVerify\"\n',
                                    '    if ! tmsh run cli script verifyHash \"$fileToVerify\"; then\n',
                                    '        echo \"$fileToVerify\" is not valid\n',
                                    '        exit 1\n',
                                    '    fi\n',
                                    '    echo verified \"$fileToVerify\"\n',
                                    'done\n',
                                    'mkdir -p /config/cloud/gce/node_modules\n',
                                    'echo expanding f5-cloud-libs.tar.gz\n',
                                    'tar xvfz /config/cloud/f5-cloud-libs.tar.gz -C /config/cloud/gce/node_modules\n',
                                    'echo expanding f5-cloud-libs-gce.tar.gz\n',
                                    'tar xvfz /config/cloud/f5-cloud-libs-gce.tar.gz -C /config/cloud/gce/node_modules/f5-cloud-libs/node_modules\n',
                                    'touch /config/cloud/cloudLibsReady\n',
                                    'EOF\n',
                                    'cat <<\'EOF\' > /config/verifyHash\n',
                                    'cli script /Common/verifyHash {\n',
                                    'proc script::run {} {\n',
                                    '        if {[catch {\n',
                                    '            set hashes(f5-cloud-libs.tar.gz) ce4f117ee84dc5e05be0bb29d2536f6e8dbb8ce3d899c1c380bdab56c9584983ddc64213ef7b1dfd305ca6ad9c830d73d4c3343256822fb500c5b77f48cf1c4e\n',
                                    '            set hashes(f5-cloud-libs-aws.tar.gz) 6fe531dfe013ba3e6e59576d8da7adf4e02c958e8ce8206c8f8a203996a4a1d60c43fa7ff55aa9a76eb53b62141cfca2e5622c555ffe94b981459f1f6cbdfbc0\n',
                                    '            set hashes(f5-cloud-libs-azure.tar.gz) d5e2e26f92f61f3917d8212b71fee55e9f58811ee488137e9c28ac54e5eb2434725696af286839e8b5ea68e05078188e0ada6e215c6c233d2585fd2acca0532d\n',
                                    '            set hashes(f5-cloud-libs-gce.tar.gz) 67e9fef439851ad4f9fbaf3f3574dadb2fceea0b13a77ccde41bcf31c42f87d6c37c64d50d685fc9a90acedc8c80abee9114b9a232809f36746bdc8e1de1b22a\n',
                                    '            set hashes(f5-cloud-libs-openstack.tar.gz) 5c83fe6a93a6fceb5a2e8437b5ed8cc9faf4c1621bfc9e6a0779f6c2137b45eab8ae0e7ed745c8cf821b9371245ca29749ca0b7e5663949d77496b8728f4b0f9\n',
                                    '            set hashes(asm-policy-linux.tar.gz) 63b5c2a51ca09c43bd89af3773bbab87c71a6e7f6ad9410b229b4e0a1c483d46f1a9fff39d9944041b02ee9260724027414de592e99f4c2475415323e18a72e0\n',
                                    '            set hashes(f5.http.v1.2.0rc4.tmpl) 47c19a83ebfc7bd1e9e9c35f3424945ef8694aa437eedd17b6a387788d4db1396fefe445199b497064d76967b0d50238154190ca0bd73941298fc257df4dc034\n',
                                    '            set hashes(f5.http.v1.2.0rc6.tmpl) 811b14bffaab5ed0365f0106bb5ce5e4ec22385655ea3ac04de2a39bd9944f51e3714619dae7ca43662c956b5212228858f0592672a2579d4a87769186e2cbfe\n',
                                    '            set hashes(f5.http.v1.2.0rc7.tmpl) 21f413342e9a7a281a0f0e1301e745aa86af21a697d2e6fdc21dd279734936631e92f34bf1c2d2504c201f56ccd75c5c13baa2fe7653213689ec3c9e27dff77d\n',
                                    '            set hashes(f5.aws_advanced_ha.v1.3.0rc1.tmpl) 9e55149c010c1d395abdae3c3d2cb83ec13d31ed39424695e88680cf3ed5a013d626b326711d3d40ef2df46b72d414b4cb8e4f445ea0738dcbd25c4c843ac39d\n',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc1.tmpl) de068455257412a949f1eadccaee8506347e04fd69bfb645001b76f200127668e4a06be2bbb94e10fefc215cfc3665b07945e6d733cbe1a4fa1b88e881590396\n',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc2.tmpl) 6ab0bffc426df7d31913f9a474b1a07860435e366b07d77b32064acfb2952c1f207beaed77013a15e44d80d74f3253e7cf9fbbe12a90ec7128de6facd097d68f\n',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc3.tmpl) 2f2339b4bc3a23c9cfd42aae2a6de39ba0658366f25985de2ea53410a745f0f18eedc491b20f4a8dba8db48970096e2efdca7b8efffa1a83a78e5aadf218b134\n',
                                    '            set hashes(asm-policy.tar.gz) 2d39ec60d006d05d8a1567a1d8aae722419e8b062ad77d6d9a31652971e5e67bc4043d81671ba2a8b12dd229ea46d205144f75374ed4cae58cefa8f9ab6533e6\n',
                                    '            set hashes(deploy_waf.sh) 1a3a3c6274ab08a7dc2cb73aedc8d2b2a23cd9e0eb06a2e1534b3632f250f1d897056f219d5b35d3eed1207026e89989f754840fd92969c515ae4d829214fb74\n',
                                    '            set hashes(f5.policy_creator.tmpl) 06539e08d115efafe55aa507ecb4e443e83bdb1f5825a9514954ef6ca56d240ed00c7b5d67bd8f67b815ee9dd46451984701d058c89dae2434c89715d375a620\n',
                                    '            set hashes(f5.service_discovery.tmpl) 592f94c6bfcf543f97632b8ac42b773e30390db77f150291815c45d7f62c30b5ade515ae7257f3bedc0329084499fdf18a6d9a93c90cade23542116edefd6849\n',
                                    '            set hashes(f5.cloud_logger.v1.0.0.tmpl) a26d5c470e70b821621476bcfd0579dbc0964f6a54158bc6314fa1e2f63b23bf3f3eb43ade5081131c24e08579db2e1e574beb3f8d9789d28acb4f312fad8c3e\n',
                                    'NEW_LINE\n',
                                    '            set file_path [lindex $tmsh::argv 1]\n',
                                    '            set file_name [file tail $file_path]\n',
                                    'NEW_LINE\n',
                                    '            if {![info exists hashes($file_name)]} {\n',
                                    '                tmsh::log err "No hash found for $file_name"\n',
                                    '                exit 1\n',
                                    '            }\n',
                                    'NEW_LINE\n',
                                    '            set expected_hash $hashes($file_name)\n',
                                    '            set computed_hash [lindex [exec /usr/bin/openssl dgst -r -sha512 $file_path] 0]\n',
                                    '            if { $expected_hash eq $computed_hash } {\n',
                                    '                exit 0\n',
                                    '            }\n',
                                    '            tmsh::log err "Hash does not match for $file_path"\n',
                                    '            exit 1\n',
                                    '        }]} {\n',
                                    '            tmsh::log err {Unexpected error in verifyHash}\n',
                                    '            exit 1\n',
                                    '        }\n',
                                    '    }\n',
                                    '    script-signature l7l44Su2uMo54s/MM/oiCj5wjjpMbHBIekX/wHVlOEN5WGnmEV6bbvkoHJRfnDFlFcP9zD2sggq4GFLswlhxZ61KDYvC46pNYhdugtdNbwRo+qQatjY1alV6wteLIlrSwACrMEcEguAvLJnLba5za3wuY8he/3yuR9d0ciOU1TC3Gi99XwJTFL1e7toMnlreRKS6Jlu+1pJhP9+3CpuUKy40BeZgCkJTd7DPZwFwpQ2udMCtkmR6NSfFMpRPb9TgOicZ7wg3BClwbXNuO3xZfPbjuuUgicHIGaDMtAIyY/01NlMCUpoFpr8CHZn6ljC+Jn+OlH/SDILfP+OH4MNcfg==\n',
                                    '    signing-key /Common/f5-irule\n',
                                    '}\n',
                                    'EOF\n',
                                    '# empty new line chars get stripped, strip out place holder NEW_LINE\n',
                                    'sed -i "s/NEW_LINE//" /config/verifyHash\n',
                                    'cat <<\'EOF\' > /config/waitThenRun.sh\n',
                                    '#!/bin/bash\n',
                                    'while true; do echo \"waiting for cloud libs install to complete\"\n',
                                    '    if [ -f /config/cloud/cloudLibsReady ]; then\n',
                                    '        break\n',
                                    '    else\n',
                                    '        sleep 10\n',
                                    '    fi\n',
                                    'done\n',
                                    '\"$@\"\n',
                                    'EOF\n',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh\n',
                                    '#!/bin/bash\n',
                                    '# Grab ip address assined to 1.1\n',
                                    'INT1ADDRESS=`curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/ip\" -H \"Metadata-Flavor: Google\"`\n',
                                    '# Determine network from self ip and netmask given\n',
                                    'prefix2mask() {\n',
                                    '   local i mask=""\n',
                                    '   local octets=$(($1/8))\n',
                                    '   local part_octet=$(($1%8))\n',
                                    '   for ((i=0;i<4;i+=1)); do\n',
                                    '       if [ $i -lt $octets ]; then\n',
                                    '           mask+=255\n',
                                    '       elif [ $i -eq $octets ]; then\n',
                                    '           mask+=$((256 - 2**(8-$part_octet)))\n',
                                    '       else\n',
                                    '           mask+=0\n',
                                    '       fi\n',
                                    '       test $i -lt 3 && mask+=.\n',
                                    '   done\n',
                                    '   echo $mask\n',
                                    '}\n',
                                    'dotmask=`prefix2mask ',
                                    context.properties['mask1'],
                                    '`\n',
                                    'IFS=. read -r i1 i2 i3 i4 <<< ${INT1ADDRESS}\n',
                                    'IFS=. read -r m1 m2 m3 m4 <<< ${dotmask}\n',
                                    'network=`printf "%d.%d.%d.%d\n" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))"`\n',
                                    'GATEWAY=$(echo "`echo $network |cut -d"." -f1-3`.$((`echo $network |cut -d"." -f4` + 1))")\n',
                                    'PROGNAME=$(basename $0)\n',
                                    'function error_exit {\n',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2\n',
                                    'exit 1\n',
                                    '}\n',
                                    'date\n',
                                    'declare -a tmsh=()\n',
                                    'echo \'starting custom-config.sh\'\n',
                                    'useServiceDiscovery=\'',
                                    context.properties['tagValue'],
                                    '\'\n',
                                    'if [ -n "${useServiceDiscovery}" ];then\n',
                                    '   tmsh+=(\n'
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\'\n',
                                    '   \'tmsh create /sys application service serviceDiscovery template f5.service_discovery variables add { basic__advanced { value no } basic__display_help { value hide } cloud__cloud_provider { value gce }  cloud__gce_region { value \"/#default#\" } monitor__frequency { value 30 } monitor__http_method { value GET } monitor__http_verison { value http11 } monitor__monitor { value \"/#create_new#\"} monitor__response { value \"\" } monitor__uri { value / } pool__interval { value 60 } pool__member_conn_limit { value 0 } pool__member_port { value 80 } pool__pool_to_use { value \"/#create_new#\" } pool__public_private {value private} pool__tag_key { value ',
                                    context.properties['tagName'],
                                    ' } pool__tag_value { value ',
                                    context.properties['tagValue'],
                                    ' } }\')\n',
                                    'else\n',
                                    '   tmsh+=(\n',
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\')\n',
                                    'fi\n',
                                    'tmsh+=(',
                                    '\"tmsh create net vlan external interfaces add { 1.1 } mtu 1460\"\n',
                                    '\"tmsh create net self ${INT1ADDRESS}/32 vlan external\"\n',
                                    '\"tmsh create net route ext_gw_int network ${GATEWAY}/32 interface external\"\n',
                                    '\"tmsh create net route ext_rt network ${network}/',
                                    context.properties['mask1'],
                                    ' gw ${GATEWAY}\"\n',
                                    '\"tmsh create net route default gw ${GATEWAY}\"\n',
                                    '\'tmsh save /sys config\'\n',
                                    '\'bigstart restart restnoded\')\n',
                                    'for CMD in "${tmsh[@]}"\n',
                                    'do\n',
                                    '    if $CMD;then\n',
                                    '        echo \"command $CMD successfully executed."\n',
                                    '    else\n',
                                    '        error_exit "$LINENO: An error has occurred while executing $CMD. Aborting!"\n',
                                    '    fi\n',
                                    'done\n',
                                    'date\n',
                                    '### START CUSTOM CONFIGURATION\n',
                                    '### END CUSTOM CONFIGURATION\n',
                                    'EOF\n',
                                    'cat <<\'EOF\' > /config/cloud/gce/rm-password.sh\n',
                                    '#!/bin/bash\n',
                                    'date\n',
                                    'echo \'starting rm-password.sh\'\n',
                                    'rm /config/cloud/gce/.adminPassword\n',
                                    'date\n',
                                    'EOF\n',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://raw.githubusercontent.com/F5Networks/f5-cloud-libs/v4.3.0/dist/f5-cloud-libs.tar.gz\n',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://raw.githubusercontent.com/F5Networks/f5-cloud-libs-gce/v2.2.0/dist/f5-cloud-libs-gce.tar.gz\n',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://raw.githubusercontent.com/F5Networks/f5-cloud-iapps/v2.1.1/f5-service-discovery/f5.service_discovery.tmpl\n',
                                    'chmod 755 /config/verifyHash\n',
                                    'chmod 755 /config/installCloudLibs.sh\n',
                                    'chmod 755 /config/waitThenRun.sh\n',
                                    'chmod 755 /config/cloud/gce/custom-config.sh\n',
                                    'chmod 755 /config/cloud/gce/rm-password.sh\n',
                                    'mkdir -p /var/log/cloud/google\n',
                                    'nohup /usr/bin/setdb provision.1nicautoconfig disable &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --signal PASSWORD_CREATED --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword\' --log-level verbose -o /var/log/cloud/google/generatePassword.log &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --wait-for PASSWORD_CREATED --signal ADMIN_CREATED --file /config/cloud/gce/node_modules/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user admin --password-file /config/cloud/gce/.adminPassword\' --log-level debug -o /var/log/cloud/google/createUser.log &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    CUSTHASH,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/onboard.js --port 443 --ssl-port ',
                                    context.properties['manGuiPort'],
                                    ' --wait-for ADMIN_CREATED -o /var/log/cloud/google/onboard.log --log-level debug --no-reboot --host localhost --user admin --password-url file:///config/cloud/gce/.adminPassword --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC --module ltm:nominal --license ',
                                    context.properties['licenseKey1'],
                                    SENDANALYTICS,
                                    ' &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config.log --log-level debug --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/rm-password.sh --cwd /config/cloud/gce -o /var/log/cloud/google/rm-password.log --log-level debug --wait-for CUSTOM_CONFIG_DONE --signal PASSWORD_REMOVED &>> /var/log/cloud/google/install.log < /dev/null &\n',
                                    'touch /config/startupFinished\n',
                                    ])
                            )
              }]
          }
      }
  }]
  outputs = [{
      'name': 'bigipIP',
      'value': ''.join(['$(ref.' + context.env['name'] + '-' + context.env['deployment'] + '.bigipIP)']),
  }]
  return {'resources': resources}
