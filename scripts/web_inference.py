from bottle import Bottle, request, response, run, static_file, HTTPResponse, redirect
import os
#import uuid
import subprocess
import hashlib
from datetime import datetime

app = Bottle()

# Directory where job output folders will be stored
BASE_OUTPUT_DIR = '/storage/Data/AF3DeepMindInferencejobs'  # Change this to your desired path
log_file = os.path.join(BASE_OUTPUT_DIR, 'AF3DeepMindInference.log')

@app.route('/favicon.ico', name='get_favicon')
def get_favicon():
    response.content_type = 'image/png'
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA+UlEQVQ4T6XSMQ5EQBQG4F8l0aiVCpE4gAIFcQaVwiX0GjeQOAAKpxARrVIpDqByANndeckmNsGO3Wllvnn/+wmP18EfR2CAqqoIwxBpmhKVJAmKosA8z19pAmzbhiiKaJqGLnieh23b0HUdH+A4DizLQhAEdKGuawzDgLZt+YEsy1CWJdhKWJw4ju8Bfd/D930anb0sSRJM06QJDMNAnueH09AOWAQGVFVFQBRFkGUZ67ryR2DA/uyBq5ZogqNndF2Hoij0aZomaJp22NIp8I7FgKuWuIGzlrgijOOIZVk+WnJdl9o6BfZ7OWrpJ2CP3gKufgauCFfAE09Z1dH0wbq/AAAAAElFTkSuQmCC"

@app.route('/AF3DeepMindInferenceIBS/previous_results', name="previous_results")
def previous_results():
    log_lines = ''
    if os.path.isfile(log_file):
        with open(log_file, 'r') as f:
            log_line = f.read()
            if(log_line != None):
                log_lines += log_line
    pagestr = '<!DOCTYPE html>'
    pagestr += '<html>'
    pagestr += '<head>'
    pagestr += '<style type="text/css" media="screen">'
    pagestr += 'th { position:sticky; top:0px; background:white;}'
    pagestr += '</style>'
    pagestr += '</head>'
    pagestr += '<body>'
    pagestr += '<p><table style="width:100%">'
    pagestr += '<th>Date-time</th><th>User</th><th>IP</th><th>Job id</th>'
    pagestr += log_lines
    pagestr += '</table></p>'
    pagestr += '</body>'
    pagestr += '</html>'
    return pagestr

@app.route('/AF3DeepMindInferenceIBS', method=['GET', 'POST'])
def index():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    log_lines = ''
    if os.path.isfile(log_file):
        with open(log_file, 'r') as f:
            log_line = f.read()
            if(log_line != None):
                log_lines += log_line
    if request.method == 'POST':
        # Get text parameters from the form
        json = request.files.get('json')
        #name, ext = os.path.splitext(json.filename)
        #if ext not in ('.json', '.JSON', '.Json'):
        #    return "File extension not allowed."
        tmp_save_path = '/storage/Data/AF3DeepMindInferencejobs/tmpjson.'+hashlib.md5(str(datetime.now()).encode("utf-8")).hexdigest()+'.json'
        with open(tmp_save_path, 'wb') as open_file:
            open_file.write(json.file.read())
        with open(tmp_save_path, 'r') as f:
            json_content = f.read()
        email = request.forms.get('email')

        # Generate a unique job ID
        job_id = hashlib.md5(json_content.encode("utf-8")).hexdigest()

        # Create an output directory for the job
        job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)
        os.makedirs(job_output_dir, exist_ok=True)

        # move json to a file inside job_output_dir
        json_file = os.path.join(job_output_dir, 'input_'+job_id+'.json')
        os.rename(tmp_save_path, json_file)

        subprocess.call(['chmod', '664', json_file])
        # Launch the subprocess asynchronously
        my_env = os.environ.copy()
        my_env["IBSJOBNAME"] = job_id
        command = ['/storage/Alphafold/scripts/alphafold3_deepmind_inference_caller.bin', json_file]
        subprocess.Popen(command, cwd=job_output_dir, env=my_env)

        # Return the job URL to the client
        job_url = request.urlparts.scheme + "://" + request.urlparts.netloc + app.get_url('job_results', job_id=job_id)
        with open(log_file, 'a') as f:
            f.write('<tr><td>'+str(datetime.now())+'</td><td>'+email.split("@")[0]+'</td><td>'+client_ip+'</td><td><a href="'+job_url+'">'+job_id+'</a></td></tr>\n')
        log_lines +='<tr><td>'+str(datetime.now())+'</td><td>'+email.split("@")[0]+'</td><td>'+client_ip+'</td><td><a href="'+job_url+'">'+job_id+'</a></td></tr>\n'
        return f'''
            <h1>Your Alphafold 3 DeepMind Inference job has been submitted</h1>
            <p>You can check the result at: <a href="{job_url}">{job_url}</a></p>
            <p>Keep the link above for future access.</p>
        '''

    # If GET request, display the submission form
    # Get the output of 'squeue'
    try:
        squeue_output = subprocess.check_output(['squeue'], universal_newlines=True)
    except subprocess.CalledProcessError as e:
        squeue_output = f"Failed to retrieve squeue output: {e}"
    pagestr = '''<!DOCTYPE html>
<html>
<head>
<style type="text/css" media="screen">
textarea:invalid {
    border: 2px dashed red;
}
textarea:valid {
    border: 2px solid black;
}
input:invalid {
    border: 2px dashed red;
}
input:valid {
    border: 2px solid black;
}
html * { text-align:center; padding:0px !important; }
table, td { border:0px solid black; border-collapse:collapse; }
p { margin:0; }
</style>
</head>
<body>
<h1>Alphafold 3 DeepMind <span style="color:red;">Inference</span> IBS server (2/2)</h1>
    <h2>step 1: MSA -> step 2: <span style="color:red;">INFERENCE</span></h2>
    <h2>Only the <span style="color:red;">INFERENCE</span> part (GPU) of the job will be done.</h2>
    <h3>(to perform the initial MSA part, go <a href="http://gre052244.ibs.fr:8083/AF3DeepMindMSAIBS" target="_blank">here</a>)</h3>
<form method="post" enctype="multipart/form-data">
    <p>JSON alphafold 3 input file according to <a href="https://github.com/google-deepmind/alphafold3/blob/main/docs/input.md" target="_blank" title="AF3 Deepmind input format/instructions">these instructions and format</a>.</p>
    <p>&nbsp;</p>
    <p>(In most cases this json file is the one produced by the <a href="http://gre052244.ibs.fr:8083/AF3DeepMindMSAIBS" target="_blank">MSA server</a>)</p>
    <p>&nbsp;</p>
    <input type="file" id="json" name="json" accept="application/json" required />
    <p>&nbsp;</p>
    <p>E-mail to get a job-done notification:</p>
    <p><input type="email" id="email" name="email" style="text-align:right;" required autocorrect="off" autocapitalize="off" spellcheck="false" pattern="^[a-z0-9._\-]+@ibs\.fr" placeholder="your_email@ibs.fr"></p>
    <p>&nbsp;</p>
    <input type="submit" value="Submit" style="font-size: 24px">
    <p>&nbsp;</p>
    <h3 style="text-align:left;">General remarks:</h3>
    <p style="text-align:left;">The MSA part takes about 15-30 min to run for EACH DIFFERENT sequence in the job.</p>
    <p style="text-align:left;">MSA calculations are INDEPENDENT, sequence per sequence. i.e. you don't need to launch all the sequences you need in a single job. You can run them by parts and combine the results later.</p>
    <p style="text-align:left;">The INFERENCE part takes about 5-15 min to run.</p>
    <p style="text-align:left;">JSON files are text ASCII files that can/should be edited carefully.</p>
    <p style="text-align:left;">Consider investing time in analyzing and consolidating the outputs of multiple independently launched MSA computation jobs into a single JSON file. This streamlined approach can significantly enhance the efficiency of subsequent INFERENCE jobs by reducing redundancy avoiding waste of time.</p>
    <p>&nbsp;</p>
</form>
    '''
    pagestr += f'''
<h2>Current Slurm job queue:</h2>
<pre>{squeue_output}</pre>
<hr/>
    '''
    pagestr += 'Your IP is: {}\n'.format(client_ip)
    pagestr += '<hr/>\n'
    pagestr += '<h2>Previous Alphafold 3 DeepMind Inference jobs:</h2>\n'
    pagestr += '<iframe title="Previous AF3 DeepMind Inference results" width="100%" height="350" src="AF3DeepMindInferenceIBS/previous_results" onload="this.contentWindow.scrollTo(0,this.contentDocument.body.scrollHeight)"></iframe>\n'
    pagestr += '</body>'
    pagestr += '</html>'
    return pagestr

@app.route('/AF3DeepMindInferenceIBS/job/<job_id>', name='job_results')
def job_results(job_id):
    job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)

    if not os.path.exists(job_output_dir):
        return HTTPResponse('Alphafold 3 DeepMind Inference job not found.', status=404)

    # Check if the job is still running
    finished_flag = os.path.join(job_output_dir, 'input_'+job_id+'_AF3DeepMindInference_IBS/finished.txt')
    running_flag = os.path.join(BASE_OUTPUT_DIR, 'input_'+job_id+'_AF3DeepMindInference_IBS/running.txt')
    failed_flag = os.path.join(job_output_dir, 'input_'+job_id+'_AF3DeepMindInference_IBS/failed.txt')

    if os.path.exists(finished_flag):
        # Job is complete; display results with a link to the file browser
        browse_url = app.get_url('browse', job_id=job_id, filepath='')
        return f'''
            <h1>Alphafold 3 DeepMind Inference job completed successfully</h1>
            <p>You can browse the output files here:</p>
            <a href="{browse_url}">Browse output files</a>
        '''
    elif os.path.exists(failed_flag):
        # Job has failed; display error message and any available logs
        error_message = ''
        error_log_path = os.path.join(job_output_dir, 'input_'+job_id+'_AF3DeepMindInference_IBS.log')
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r') as f:
                error_message = f.read()
        return f'''
            <h1>Alphafold 3 DeepMind Inference job failed</h1>
            <p>An error occurred during the job execution.</p>
            <h2>Error Details:</h2>
            <pre>{error_message}</pre>
        '''
    elif os.path.exists(running_flag):
        # Job is still running or did not start yet
        # Get the output of 'nvidia-smi'
        try:
            nvidia_smi_output = subprocess.check_output(['nvidia-smi'], universal_newlines=True)
        except subprocess.CalledProcessError as e:
            nvidia_smi_output = f"Failed to retrieve nvidia-smi output: {e}"
        # Get the output of 'squeue'
        try:
            squeue_output = subprocess.check_output(['squeue'], universal_newlines=True)
        except subprocess.CalledProcessError as e:
            squeue_output = f"Failed to retrieve squeue output: {e}"

        # Return the page indicating the job is still running or in the queue and display nvidia-smi/squeue output
        return f'''
            <h1>Alphafold 3 DeepMind Inference job is still running or is in the queue.</h1>
            <p>Please refresh this page later.</p>
            <h2>Current Slurm job queue:</h2>
            <pre>{squeue_output}</pre>
            <h2>GPU Status:</h2>
            <pre>{nvidia_smi_output}</pre>
        '''
    else:
        # Job failed to start
        return f'''
            <h1>Alphafold 3 DeepMind Inference job is not running nor in the queue. (PROBLEM?)</h1>
            <p>Please refresh this page later.</p>
            <p>If this persists, contact leandro.estrozi@ibs.fr</p>
        '''

@app.route('/AF3DeepMindInferenceIBS/browse/<job_id>/<filepath:path>', name='browse_sub')
@app.route('/AF3DeepMindInferenceIBS/browse/<job_id>', name='browse')
def browse(job_id, filepath=''):
    job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)

    if not os.path.exists(job_output_dir):
        return HTTPResponse('Job not found.', status=404)

    # Ensure that the filepath is within the job_output_dir
    safe_root = os.path.abspath(job_output_dir)
    requested_path = os.path.abspath(os.path.join(job_output_dir, filepath))

    if not requested_path.startswith(safe_root):
        return HTTPResponse('Access denied.', status=403)

    if os.path.isdir(requested_path):
        # List directory contents
        items = os.listdir(requested_path)
        items.sort()
        item_links = []
        for item in items:
            item_path = os.path.join(filepath, item)
            fsize = os.path.getsize(os.path.join(requested_path, item))
            if os.path.isdir(os.path.join(requested_path, item)):
                item_url = app.get_url('browse_sub', job_id=job_id, filepath=item_path)
                item_links.append(f'<li><pre style="display:inline">drwxr-xr-x </pre>[<a href="{item_url}">RESULTS</a>] {item}</li>')
            else:
                download_url = app.get_url('download_file', job_id=job_id, filepath=item_path)
                # Check if the file is a PNG image
                if item.lower().endswith('.png'):
                    view_url = app.get_url('view_image', job_id=job_id, filepath=item_path)
                else:
                    view_url = app.get_url('view_file', job_id=job_id, filepath=item_path)
                item_links.append(f'<li><pre style="display:inline">-rw-r--r-- </pre>[<a href="{download_url}">Download</a>] {item} [<a href="{view_url}" target="_blank">View</a>] {fsize} bytes</li>')

        # Navigation links
        nav_links = ''
        if filepath:
            parent_path = os.path.dirname(filepath)
            if parent_path:
                # Use 'browse_sub' route when parent_path is not empty
                parent_url = app.get_url('browse_sub', job_id=job_id, filepath=parent_path)
            else:
                # Use 'browse' route when parent_path is empty
                parent_url = app.get_url('browse', job_id=job_id)
            nav_links = f'<a href="{parent_url}">[Parent Directory]</a>'

        return f'''
            <h1><a href="http://{os.uname()[1]}.ibs.fr:8084/AF3DeepMindInferenceIBS" target="_top">Alphafold 3 DeepMind Inference IBS server</a></h1>
            <h1>Browsing Alphafold3 DeepMind Inference results: {filepath or job_id}</h1>
            {nav_links}
            <ul>
                {''.join(item_links)}
            </ul>
        '''
    elif os.path.isfile(requested_path):
        # If a file is requested, serve it for download 
        return download_file(job_id, filepath)
    else:
        return HTTPResponse('File or directory not found.', status=404)

@app.route('/AF3DeepMindInferenceIBS/download/<job_id>/<filepath:path>', name='download_file')
def download_file(job_id, filepath):
    job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)

    # Ensure that the filepath is within the job_output_dir
    safe_root = os.path.abspath(job_output_dir)
    requested_file = os.path.abspath(os.path.join(job_output_dir, filepath))

    if not requested_file.startswith(safe_root):
        return HTTPResponse('Access denied.', status=403)

    if not os.path.exists(requested_file):
        return HTTPResponse('File not found.', status=404)

    return static_file(
        os.path.basename(requested_file),
        root=os.path.dirname(requested_file),
        download=os.path.basename(requested_file)
    )

@app.route('/AF3DeepMindInferenceIBS/view_image/<job_id>/<filepath:path>', name='view_image')
def view_image(job_id, filepath):
    job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)

    # Ensure that the filepath is within the job_output_dir
    safe_root = os.path.abspath(job_output_dir)
    requested_file = os.path.abspath(os.path.join(job_output_dir, filepath))

    if not requested_file.startswith(safe_root):
        return HTTPResponse('Access denied.', status=403)

    if not os.path.isfile(requested_file):
        return HTTPResponse('Image not found.', status=404)

    # Serve the image file without download prompt
    return static_file(
        os.path.basename(requested_file),
        root=os.path.dirname(requested_file),
        mimetype='image/png'
    )

@app.route('/AF3DeepMindInferenceIBS/view_file/<job_id>/<filepath:path>', name='view_file')
def view_file(job_id, filepath):
    job_output_dir = os.path.join(BASE_OUTPUT_DIR, job_id)

    # Ensure that the filepath is within the job_output_dir
    safe_root = os.path.abspath(job_output_dir)
    requested_file = os.path.abspath(os.path.join(job_output_dir, filepath))

    if not requested_file.startswith(safe_root):
        return HTTPResponse('Access denied.', status=403)

    if not os.path.isfile(requested_file):
        return HTTPResponse('Image not found.', status=404)

    # Serve the image file without download prompt
    return static_file(
        os.path.basename(requested_file),
        root=os.path.dirname(requested_file),
        mimetype='text/plain'
    )

@app.route('/AF3DeepMindInferenceIBS/')
def wrong():
    redirect("/AF3DeepMindInferenceIBS")

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8084, debug=True, reloader=True)
#    run(app, host='0.0.0.0', port=8084, debug=False)
