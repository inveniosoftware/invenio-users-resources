#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


# Usage:
#   env DB=postgresql12 SEARCH=opensearch2 CACHE=redis MQ=rabbitmq ./run-tests.sh

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

keep_services=0
pytest_args=()
for arg in $@; do
	# from the CLI args, filter out some known values and forward the rest to "pytest"
	# note: we don't use "getopts" here b/c of some limitations (e.g. long options),
	#       which means that we can't combine short options (e.g. "./run-tests -Kk pattern")
	case ${arg} in
		-K|--keep-services)
			keep_services=1
			;;
		*)
			pytest_args+=( ${arg} )
			;;
	esac
done


# Always bring down docker services
function cleanup() {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

python -m check_manifest
python -m setup extract_messages --output-file /dev/null
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --db ${DB:-postgresql} --search ${SEARCH:-opensearch} --cache ${CACHE:-redis} --mq ${MQ:-rabbitmq} --env)"
python -m pytest ${pytest_args[@]+"${pytest_args[@]}"}
tests_exit_code=$?
exit "$tests_exit_code"
