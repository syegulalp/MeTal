% include('sidebar/page_taglist.tpl')
<div id="tags_group" class="form-group has-feedback">
    <input type="text" class="form-control input-sm enteradd typeahead"
    id="tag_input" placeholder="Type tags here" name="tag_input" value="" data-cip-id="tag_input">
    <span id="tag_activity" style="display:none" class="glyphicon glyphicon-refresh form-control-feedback"></span>
</div>
<small><a target="_blank" href="{{settings.BASE_URL}}/blog/{{blog.id}}/tags">See all tags for this blog</a></small>
<input type="hidden" id="tag_text" name="tag_text">
<input type="hidden" id="new_tags" name="new_tags">