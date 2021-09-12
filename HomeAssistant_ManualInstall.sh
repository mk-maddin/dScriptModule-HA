#!/bin/bash
# version: 2019.12.29
# description: manually copy and install the dScriptModule to HA server for test

##-- save maximum error code
error=0; trap 'error=$(($?>$error?$?:$error))' ERR

##--meta-information required paramteres
scriptAuthor="Martin Kraemer, mk.maddin@gmail.com"
scriptName=$( basename "$0" )
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

##--default values for parameters
SSH_host="192.168.33.12"
SSH_pass='12345678'
SSH_user="root"
verbose=""
component="dscriptmodule"
package="dscript"
ha_path="/usr/share/hassio/homeassistant"

##--help text and script parameter processing
for i in "$@";do
case $i in
	-h|--help) #help parameter for command
	echo ""
	echo "$scriptName" 
	echo "by $scriptAuthor" 
	echo ""
	echo "Usage: $scriptName [parameter]=[value]"
	echo ""
	echo "Parameter:"
	echo -e "\t -h \t| --help \t\t-> shows this help information"
	echo -e "\t -v \t| --verbose \t\t-> enable verbose ouput"
	echo -e "\t -c= \t| --component= \t\t-> defines the component name to perform selected action on (default is: $component)"
	echo -e "\t -k= \t| --package= \t\t-> defines the package name to perform selected action on (default is: $package)"
	echo -e "\t -h= \t| --host= \t\t-> hostname/IP-address of host to perform mode on (default is: $SSH_host)"
	echo -e "\t -u= \t| --user= \t\t-> username for ssh access to remote host (default is: $SSH_user)"
	echo -e "\t -p=  \t| --pass= \t\t-> password for ssh access to remote host (default is: $SSH_pass)"
	echo -e ""
	echo ""
	echo "Description:"
	echo "Manually copy and install this module to a home assistant server with docker installation"
	echo ""
	exit 0;;
	-v|--verbose)
	verbose="-v"
	shift;;
	-c=*|--component=*)
	component="${i#*=}"
	shift;;
	-k=*|--package=*)
	package="${i#*=}"
	shift;;
	-h=*|--host=*)
	SSH_host="${i#*=}"
	shift;;
	-u=*|--user=*)
	SSH_user="${i#*=}"
	shift;;
	-p=*|--pass=*)
	SSH_pass="${i#*=}"
	shift;;
	*)  # unknown option
	>&2 echo "$scriptName: error: invalid option: $i" 
	>&2 echo "Try '$scriptName --help' for more information."
	exit 22;;
esac;done


folder="${scriptDir}/custom_components/${component}"
if [ -d "${folder}" ];then
	echo "I: process: ${folder##${scriptDir}}"
	target="${ha_path}${folder##${scriptDir}}"
	sshpass -p "$SSH_pass" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${SSH_user}@${SSH_host}" << EOF
		if [ -d "${target}" ];then
			echo "I: delete old: ${target}"
			rm -rf "${target}"
		fi
EOF
	sshpass -p "$SSH_pass"	scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "${folder}" "${SSH_user}@${SSH_host}:$(dirname ${target})"
fi


folder="${scriptDir}/packages/${package}"
if [ -d "${folder}" ];then
	echo "I: process: ${folder##${scriptDir}}"
	target="${ha_path}${folder##${scriptDir}}"
	sshpass -p "$SSH_pass" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${SSH_user}@${SSH_host}" << EOF
		if [ -d "${target}" ];then
			echo "I: delete old: ${target}"
			rm -rf "${target}"
		fi
EOF
	sshpass -p "$SSH_pass"	scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "${folder}" "${SSH_user}@${SSH_host}:$(dirname ${target})"
fi

sshpass -p "$SSH_pass" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${SSH_user}@${SSH_host}" << EOF
	echo "I: reload to apply newly copied component"
	hassio-reload.sh
EOF


exit "$error"
