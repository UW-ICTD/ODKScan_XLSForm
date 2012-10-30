from django.http import HttpResponse
from django.shortcuts import render_to_response
from django import forms

import datetime
import tempfile
import os

import form_creator

SERVER_TMP_DIR = '/tmp'

class UploadFileForm(forms.Form):
    file  = forms.FileField()

def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            error = None
            warnings = None
            paths = []
            
            filename, ext = os.path.splitext(request.FILES['file'].name)
            
            #Make a randomly generated directory to prevent name collisions
            temp_dir = tempfile.mkdtemp(dir=SERVER_TMP_DIR)
            out_path = os.path.join(temp_dir, filename)
            
            try:
                warnings = []
                paths = form_creator.create_form(request.FILES['file'], out_path)
                
            except Exception as e:
                error = 'Error: ' + str(e)
            
            return render_to_response('upload.html', {
                'form': UploadFileForm(),
                'paths': [os.path.relpath(path, SERVER_TMP_DIR) for path in paths],
                'error': error,
                'warnings': warnings,
            })
        else:
            #Fall through and use the invalid form
            pass
    else:
        form = UploadFileForm() #Create a new empty form
        
    return render_to_response('upload.html', {
        'form': form,
    })

def download(request, path):
    import StringIO
    import zipfile
    
    name = os.path.split(path)[-1]
    zip_filename = "%s.zip" % name
    zipFileBuffer = StringIO.StringIO()
    zf = zipfile.ZipFile(zipFileBuffer, "w")

    for root, dirs, files in os.walk(os.path.join(SERVER_TMP_DIR, path)):
        for file in files:
            filepath = os.path.join(root, file)
            filepath_without_base_dirs = os.path.join(*filter(lambda x: x, filepath.split('/'))[2:])
            zf.write(filepath, filepath_without_base_dirs)

    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    response = HttpResponse(zipFileBuffer.getvalue(), mimetype = "application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return response

def serve_json(request, path):
    """
    Serve a downloadable file
    """
    fo = open(os.path.join(SERVER_TMP_DIR, path))
    data = fo.read()
    fo.close()
    response = HttpResponse(mimetype="application/json")
    response.write(data)
    return response