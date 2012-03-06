#!/bin/bash
# 2012-03-06 Aurelio Jargas, Public Domain

PROJ_ROOT=".."
ML_PATH="moneylog-svn"  # where's the MoneyLog SVN?
ML_PATH="/a/www/moneylog/svn"
SAMPLE_TXT="$ML_PATH"/sample/data-pt.txt

die() { echo "$*"; exit 1; }
msg() { echo "****** $*"; }

# Make sure we're on the util folder
cd $(dirname "$0")

# Sanity
test -d "$ML_PATH"    || die "Cannot find folder $ML_PATH"
test -f "$SAMPLE_TXT" || die "Cannot find file $SAMPLE_TXT"

msg "Updating SVN copy"
svn update "$ML_PATH" || die

msg "Generating HTML template"
"$ML_PATH"/util/gen-cloud > "$PROJ_ROOT"/templates/moneylog.html || die

msg "Generating CONFIG template"
"$ML_PATH"/util/gen-cloud-config > "$PROJ_ROOT"/samples/moneylog_config.js || die

msg "Updating TXT sample"
control_m=$(printf '\r')
sed "s/$control_m*$//" "$SAMPLE_TXT" > "$PROJ_ROOT"/samples/moneylog_rawdata.txt || die
# dos2unix: remove CR

msg "ALL DONE."
