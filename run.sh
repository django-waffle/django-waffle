#!/bin/bash

export PYTHONPATH=".:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="test_settings"

usage() {
    echo "USAGE: $0 [command]"
    echo "  test - run the waffle tests"
    echo "  lint - run ruff"
    echo "  typecheck - run mypy"
    echo "  shell - open the Django shell"
    echo "  makemigrations - create a schema migration"
    exit 1
}

CMD="$1"
shift

case "$CMD" in
    "test" )
        DJANGO_SETTINGS_MODULE=test_settings django-admin test waffle $@ ;;
    "lint" )
        ruff . ;;
    "typecheck" )
        mypy waffle $@ ;;
    "shell" )
        django-admin shell $@ ;;
    "makemigrations" )
        django-admin makemigrations waffle $@ ;;
    "makemessages" )
        export DJANGO_SETTINGS_MODULE= && cd waffle && django-admin makemessages --all && cd - ;;
    "compilemessages" )
        export DJANGO_SETTINGS_MODULE= && cd waffle && django-admin compilemessages && cd - ;;
    "find_uncommitted_translations" )
        git diff --exit-code -G "^(msgid|msgstr)" || (echo "Please run ./run.sh makemessages and commit the updated django.po file." && false) ;;
    * )
        usage ;;
esac
