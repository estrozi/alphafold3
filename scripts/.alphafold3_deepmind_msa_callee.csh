#!/bin/tcsh -f
# Author: Leandro F. Estrozi, Institut de Biologie Structurale, Grenoble, CNRS.
# This script runs Alphafold3 from deepmind (MSA only!)
# This script places its outputs in the current folder but it also uses /storage/Data/AF3DeepMindMSAjobs as a temporary space.

#REMINDER: the caller add two arguments (uid,jobname) before the jsonfile

umask 113; # rw-rw-r--

set caller = "/storage/Alphafold/scripts/alphafold3_deepmind_msa_caller.bin"
  if($#argv < 3) then
echo "Usage: $caller jsonfile"; 
echo "";
exit 0;
  endif

onintr failed;

set u = $1;
set g = 7182;

set jobname = $2;

set json = $3;
  if( ! -e $json || -z $json ) then
echo "ERROR: jsonfile not found";
goto failed;
  endif

set name = `grep -e '^ *[\\'\"]name[\\'\"] *:.\+,$' ${json} | awk -v FS=':' '{print tolower(gensub(/[,"\047]/,"","g",$2)) }'`;
set outdir = ${json:t:r}"_AF3DeepMindMSA_IBS";
set outdir2 = /storage/Data/AF3DeepMindMSAjobs/$outdir;

# 1) To clone the IBS AF3DeepMind repository:
# #>git clone https://github.com/estrozi/alphafold3.git
# 2) To build the IBS AF3DeepMind Docker image (as a ADMIN you need to be in docker group):
# #>cd alphafold3/
# #>docker build --build-arg GNAME=ibs-gdt-iaaccess --build-arg GID=7182 --build-arg UNAME=`id -un` -f docker/Dockerfile -t alphafold3 .
set AF3DeepMindMSA_CMD = "srun -J ${jobname} docker run --user "0":"${g}" --rm --volume /storage:/app/storage --volume /storage/Alphafold3/data:/root/public_databases --gpus all alphafold3 python run_alphafold.py --model_dir=/app/storage/Alphafold3/models --db_dir=/root/public_databases --jax_compilation_cache_dir /app/storage/Alphafold3/jax_cache --norun_inference";

  if( -e $outdir) then
    if( ! -e $outdir2 ) then
echo "Moving already existing output folder $outdir to $outdir2"
echo "(it will be moved back in the end if everything goes fine)"
mv $outdir $outdir2;
if($status) goto failed;
    else
echo "Conflict: Both $outdir and $outdir2 exit. Aborting..." | tee -a $outdir.log;
goto failed;
    endif
rm -f $outdir2/finished.txt;
  else
mkdir -m 775 $outdir2;
chown ${u}:${g} $outdir2;
if($status) goto failed;
  endif

chmod 770 $outdir2;
if($status) goto failed;
chgrp 7182 $outdir2;
if($status) goto failed;
echo 0 >! $outdir2/running.txt;
if($status) goto failed;
chown ${u}:${g} $outdir2/running.txt
if($status) goto failed;

  if( -e $outdir2/${name}/${name}_data.json && ! -z $outdir2/${name}/${name}_data.json ) then
echo "Final json file found. Aborting..."
echo "This probably means that this prediction was already calculated before."
echo "Moving $outdir2 to $outdir"
rm -f $outdir2/running.txt;
if($status) goto failed;
echo 0 >! $outdir2/finished.txt;
if($status) goto failed;
chown ${u}:${g} $outdir2/finished.txt
if($status) goto failed;
mv $outdir2 $outdir;
if($status) goto failed;
exit 0;
  endif

cp -a $json /storage/Data/AF3DeepMindMSAjobs/${json:t};
if($status) goto failed;

eval $AF3DeepMindMSA_CMD" --json_path=/app/storage/Data/AF3DeepMindMSAjobs/${json:t} --output_dir=/app${outdir2}" |& tee -a $outdir.log;
if($status) goto failed;
    
chown ${u}:${g} $outdir.log;
if($status) goto failed;

chown -R ${u}:${g} $outdir2;
if($status) goto failed;

rm -f $outdir2/running.txt;
if($status) goto failed;

  if(-e /storage/Data/AF3DeepMindMSAjobs/AF3DeepMindMSA.log ) then
grep $jobname /storage/Data/AF3DeepMindMSAjobs/AF3DeepMindMSA.log | awk -v FS="<td>" '{print $3}' | sed -e 's/<\/td>//' >& /dev/null;
    if($status) then
echo "${caller}: grep jobname failed." |& tee -a $outdir.log;
    else
set email = `grep $jobname /storage/Data/AF3DeepMindMSAjobs/AF3DeepMindMSA.log | awk -v FS="<td>" '{print $3}' | sed -e 's/<\/td>//'`
set hostname = `hostname`;
set email = "${email}@ibs.fr"
sudo -u \#50809 mail -s '[no-reply] AF3DeepMind MSA results' -c leandro.estrozi@ibs.fr -- $email << EOF
AF3DeepMind MSA (CPU) results are ready.\n
\n
You can downdload them at:\n
http://${hostname}.ibs.fr:8083/AF3DeepMindMSAIBS/browse/${jobname}?filepath=\n
\n
The next step might be to launch a inference (GPU) job (based on the result above) at our AF3DeepMind Inference server:\n
\n
http://${hostname}.ibs.fr:8084/AF3DeepMindInferenceIBS\n
\n
We remind you that for the inference to work you will need a json file containing ALL the precalcuated MSAs for EACH ONE of the sequences used.\n
\n
More information at:\n
https://github.com/google-deepmind/alphafold3/blob/main/docs/input.md\n
EOF
if($status) echo "${caller}: send mail failed." |& tee -a $outdir.log;
    endif
  endif

echo 0 >! $outdir2/finished.txt;
if($status) goto failed;
chown ${u}:${g} $outdir2/finished.txt
if($status) goto failed;
echo "Moving $outdir2 to $outdir" |& tee -a $outdir.log;
mv $outdir2 $outdir;
if($status) goto failed;
chown -R ${u}:${g} $outdir;
if($status) goto failed;
rm -f /storage/Data/AF3DeepMindMSAjobs/${json:t};
if($status) goto failed;

exit 0;

failed:
echo "last cmd before fail: $_" >! $outdir2/failed.txt;
chown ${u}:${g} $outdir2/failed.txt
chown ${u}:${g} $outdir.log
echo "Moving $outdir2 to $outdir" |& tee -a $outdir.log;
mv $outdir2 $outdir;
rm -f /storage/Data/AF3DeepMindMSAjobs/${json:t};
exit 1;
