#!/bin/bash

pushd "$(dirname "${BASH_SOURCE[0]}")"
PARENT_PATH="$(pwd -P)"
popd
AUTH_SECRET_NAME=hpecp-ext-auth-secret
AUTH_SECRET_NAMESPACE=hpecp
DEX_CONFIG_FILE="${PARENT_PATH}/kubeflow-cm-dex.yaml"

function set_group_search_to_config() {
	echo "Preparing groups search settings..."

	if local result="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.groups}")"; then
	    local group="$result"
	else
		local error_message="$result"
		echo "$error_message"
		exit 1
	fi

	#remove parameters from config if group is not defined
	if [ -z "${group}" ]; then
		config="$(echo "$config" | sed "/groupSearch:/d")"
		config="$(echo "$config" | sed "/groupBaseDN:/d")"
		config="$(echo "$config" | sed "/groupFilter:/d")"
		config="$(echo "$config" | sed "/userMatchers:/d")"
		config="$(echo "$config" | sed "/userAttr:/d")"
		config="$(echo "$config" | sed "/groupAttr:/d")"
		config="$(echo "$config" | sed "/groupNameAttr:/d")"
		return
	fi

	group="$(base64 --decode <<< ${group})"

	if [[ "$group" == *"::::"* ]]; then
		#for multiple group that are separeted by ::::
		group="$(echo "$group" | sed 's/::::/;/')"

		local groups
		IFS=';' read -a groups <<< "$group"

		#fetching group base dn and verifing that all groups have the same base dn (restriction of dex)
		local group_base_dn="none"
        for one_of_groups in "${groups[@]}"; do
        	group_root_dn="$(echo "$one_of_groups" | cut -d ',' -f2-)"

        	if [[ "$group_base_dn" == "none" ]]; then
        		group_base_dn="$group_root_dn"
        	fi

        	if [[ "$group_root_dn" != "$group_base_dn" ]]; then
        		echo "[ERROR]   'groups': \"$(echo "$group" | sed 's/;/::::/')\" contains groups with different base DN"
        		exit 1
        	fi
        done

        #creating filter from first parameter in groups dn
		local filter="\"(|"
        for one_of_groups in "${groups[@]}"; do
        	group_cn="$(echo "$one_of_groups" | cut -d ',' -f1)"
        	filter="$filter($group_cn)"
        done
        filter="$filter)\""

	else
		#for single group
		local filter="\"($(echo "$group" | cut -d ',' -f1))\""
		local group_base_dn="$(echo "$group" | cut -d ',' -f2-)"
	fi

	config="$(echo "$config" | sed "s/groupBaseDN:/baseDN: $group_base_dn/")"
	config="$(echo "$config" | sed "s/groupFilter:/filter: $filter/")"
	config="$(echo "$config" | sed "s/groupNameAttr:/nameAttr:/")"

	echo "Group search settings cofigured!"
}

function set_user_search_to_config() {
	echo "Preparing user search settings..."

	local user_base_dn="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.base_dn}")"
	if [ -z "${user_base_dn}" ]; then
		echo -e "[ERROR]   'base_dn' is not found in secret"
		exit 1
	else
		user_base_dn="$(base64 --decode <<< ${user_base_dn})"
	fi

	local username="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.user_attr}")"
	if [ -z "${username}" ]; then
		echo -e "[ERROR]   'user_attr' is not found in secret"
		exit 1
	else
		username="$(base64 --decode <<< ${username})"
		username="${username,,}"
	fi

	config="$(echo "$config" | sed "0,/baseDN:/ s/baseDN:/baseDN: $user_base_dn/")"
	config="$(echo "$config" | sed "s/username:/username: $username/")"
	config="$(echo "$config" | sed "0,/nameAttr:/ s/nameAttr:/nameAttr: $username/")"

	echo "User search settings cofigured!"
}

function set_secure_to_config() {
	echo "Preparing security settings..."

	if [[ "$security_protocol" == "none" ]]; then
		config="$(echo "$config" | sed "s/startTLS:/startTLS: false/")"
	    config="$(echo "$config" | sed "s/insecureNoSSL:/insecureNoSSL: true/")"
        config="$(echo "$config" | sed "s/insecureSkipVerify:/insecureSkipVerify: true/")"
	    config="$(echo "$config" | sed "/rootCAData:/d")"

	    echo "Security settings cofigured!"
	    return
	fi

	config="$(echo "$config" | sed "s/insecureNoSSL:/insecureNoSSL: false/")"

	local root_ca_data="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.ca_cert}")"
	
	if [[ -z "$root_ca_data" ]]; then 
		config="$(echo "$config" | sed "s/insecureSkipVerify:/insecureSkipVerify: true/")"
		config="$(echo "$config" | sed "/rootCAData:/d")"
	else
		config="$(echo "$config" | sed "s/insecureSkipVerify:/insecureSkipVerify: false/")"
		config="$(echo "$config" | sed "s/rootCAData:/rootCAData: $root_ca_data/")"
	fi


	if [[ "$security_protocol" == "ldaps" ]]; then
		config="$(echo "$config" | sed "s/startTLS:/startTLS: false/")"
	elif [[ "$security_protocol" == "starttls" ]]; then
		config="$(echo "$config" | sed "s/startTLS:/startTLS: true/")"
	fi

	echo "Security settings cofigured!"
}

function escape_sed_match_pattern() {
	local pattern="$1"
	#add a '\' before each symbol that could affect sed search/replace pattern
	local result="$(echo "$pattern" | sed -e 's/[]\/$*.^[]/\\&/g')"
	echo "$result"
}

function escape_sed_replace_pattern() {
        local pattern="$1"
        #add a '\' before each symbol that could affect sed search/replace pattern
        local result="$(echo "$pattern" | sed -e 's/[\/&]/\\&/g')"
        echo "$result"
}

function set_bind_to_config() {
	echo "Preparing bind settings..."

	#check for direct_bind type. Currently is not supported by DEX LDAP connector
	if [[ "$bind_type" != "search_bind" ]]; then
		echo "[ERROR]    Bind type: '$bind_type' is not supported."
		exit 1
	fi

	local bind_dn="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.bind_dn}")"

	#anonymous search bind
	if [ -z "${bind_dn}" ]; then
		config="$(echo "$config" | sed "/bindDN:\|bindPW:/d")"
		return
	fi

	bind_dn="$(base64 --decode <<< ${bind_dn})"

	local bind_pw="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.bind_pwd}")"
	if [ -z "${bind_pw}" ]; then
		echo -e "[ERROR]   'bind_pwd' is not found in secret"
		exit 1
	else
		bind_pw="$(base64 --decode <<< ${bind_pw})"
		bind_pw="$(escape_sed_replace_pattern "$bind_pw")"
	fi

	config="$(echo "$config" | sed "s/bindDN:/bindDN: $bind_dn/")"
	config="$(echo "$config" | sed "s/bindPW:/bindPW: $bind_pw/")"

	echo "Bind settings cofigured!"
}

function set_host_to_config() {
	echo "Preparing host settings..."

	local host="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.auth_service_locations}")"
	if [ -z "${host}" ]; then
		echo -e "[ERROR]   'auth_service_locations' is not found in secret"
		exit 1
	else
		host="$(base64 --decode <<< ${host})"
	fi
	config="$(echo "$config" | sed "s/host:/host: $host/")"

	echo "Host settings cofigured!"
}

function get_config_for_ldap() {
	echo "Preparing config for LDAP..."
	set_host_to_config
	set_bind_to_config
	set_secure_to_config
    set_user_search_to_config
    set_group_search_to_config
}

function get_config_for_ad() {
	echo "Preparing config for Active Directory..."

	config="$(echo "$config" | sed "s/id: ldap/id: ad/")"
	config="$(echo "$config" | sed "s/name: LDAP/name: ActiveDirectory/")"
	config="$(echo "$config" | sed "s/idAttr: uid/idAttr: DN/")"
	config="$(echo "$config" | sed "s/emailAttr: uid/emailAttr: cn/")"

	set_host_to_config
	set_bind_to_config
	set_secure_to_config
    set_user_search_to_config
    set_group_search_to_config
}

function get_auth_type_info() {
    echo "Defining auth type..."

	directory_server="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.type}")"
	if [ -z "${directory_server}" ]; then
		echo -e "[ERROR]   'type' is not found in secret"
		exit 1
	else
		directory_server="$(base64 --decode <<< ${directory_server})"
	fi

	security_protocol="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.security_protocol}")"
	if [ -z "${security_protocol}" ]; then
		echo -e "[ERROR]   'security_protocol' is not found in secret"
		exit 1
	else
		security_protocol="$(base64 --decode <<< ${security_protocol})"
	fi

	bind_type="$(kubectl get secret -n $AUTH_SECRET_NAMESPACE $AUTH_SECRET_NAME -o jsonpath="{.data.bind_type}")"
	if [ -z "${bind_type}" ]; then
		echo -e "[ERROR]   'bind_type' is not found in secret"
		exit 1
	else
		bind_type="$(base64 --decode <<< ${bind_type})"
	fi
}


function main() {
	echo "Reading secret $AUTH_SECRET_NAME from namespace $AUTH_SECRET_NAMESPACE..."

	get_auth_type_info

	local config="$(cat $DEX_CONFIG_FILE)"

	if [[ "${security_protocol}" == "none" ]]; then
		echo "Found settings for ${directory_server} without security connection and bind type: ${bind_type}"
	else
		echo "Found settings for ${directory_server} without security security connection: ${security_protocol} and bind type: ${bind_type}"
	fi

	if [[ "${directory_server}" == "LDAP" ]]; then
		get_config_for_ldap
	elif [[ "${directory_server}" == "Active Directory" ]]; then
		get_config_for_ad
	fi

	echo "Config created! Setting up it to config map..."

	local result=`echo "${config}" | kubectl apply -f -`

	echo "$result"
	if [ $? -ne 0 ]; then
		exit 1
	fi

	echo "Success!"
}

main
exit 0
