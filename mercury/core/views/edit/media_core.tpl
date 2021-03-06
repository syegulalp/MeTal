<form class="form-horizontal" method="post">
{{!csrf_token}}

    <div class="form-group">
        <label for="media_name" class="col-sm-2 control-label">Image</label>
        <div class="col-sm-10">
            <p><img id="media_name"
            class="img-responsive img-edit-preview"
            style="max-height: 50vh"
            src="{{media.preview_url}}">
            </p>
            % c=media.pages.count()
            % if c>0:
            <p><a target="_blank" href="{{settings.BASE_URL}}/blog/{{blog.id}}/media/{{media.id}}/pages"><span class="label label-info">See all {{c}} page(s) that use this media</span></a></p>
            % else:
            <p>[<i>This media is not associated with any page in this blog.</i>]</p>
            % end
            
        </div>
    </div>
    
    <div class="form-group">
        <label for="media_filename" class="col-sm-2 control-label">File name</label>
        <div class="col-sm-10">
            <input type="text" class="form-control" aria-describedby="media_filename_help"
            value="{{media.filename}}"
            id="media_filename" name="media_filename">
            <span id="media_filename_help" class="help-block">The name of the file used by this media (if any)</span>
        </div>
    </div>

    <div class="form-group">
        <label for="media_friendly_name" class="col-sm-2 control-label">Friendly name</label>
        <div class="col-sm-10">
            <input type="text" class="form-control" aria-describedby="media_friendly_name_help"
            value="{{media.friendly_name}}"
            id="media_friendly_name" name="media_friendly_name">
            <span id="media_friendly_name_help" class="help-block">Used to describe the image ("Last Friday's lunch")</span>
        </div>
    </div>
   
    <div class="form-group">
        <label for="media_path" class="col-sm-2 control-label">File path</label>
        <div class="col-sm-10">
            <input type="text" disabled class="form-control" aria-describedby="media_path_help"
            id="media_path" name="media_path" value="{{media.path}}">
            <span id="media_path_help" class="help-block">Full path to the file for this media object. (This cannot be changed.)</span>
        </div>
    </div>      

    <div class="form-group">
        <label for="media_url" class="col-sm-2 control-label">URL</label>
        <div class="col-sm-10">
            <input type="text" disabled class="form-control" aria-describedby="media_url_help"
            id="media_url" name="media_url" value="{{media.url}}">
            <span id="media_url_help" class="help-block">URL for this media object. (This is automatically generated and cannot be changed.)</span>
        </div>
    </div>
    
    <hr/>    
    
    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-10">
            <button type="submit" class="btn btn-primary">Save changes</button>
            <span class='pull-right'>
                <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/media/{{media.id}}/delete"><button type="button" name="delete" class="btn btn-danger">Delete from server</button></a>
            </span>            
        </div>
    </div>
    
</form>

