% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-xs-12">
<form class="form-horizontal" method="post">
{{!csrf_token}}
    <div class="form-group">
        <label for="theme_title" class="col-sm-2 control-label">Theme name</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="theme_title_help"
            value="{{theme_title}}"
            id="theme_title" name="theme_title">
            <span id="theme_title_help" class="help-block">Pick a name to save this theme as.</span>
        </div>
    </div>

    <div class="form-group">
        <label for="theme_description" class="col-sm-2 control-label">Theme description</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="theme_description_help"
            value="{{theme_description}}"
            id="theme_description" name="theme_description">
            <span id="theme_description_help" class="help-block">A short description for this theme.</span>
        </div>
    </div>    
    
    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-8">
            <button type="submit" class="btn btn-primary">Save changes</button>
         
        </div>
    </div>
</form>
<hr/>
</div>
% include('include/footer.tpl')