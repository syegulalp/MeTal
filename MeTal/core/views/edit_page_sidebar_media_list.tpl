% if page.media.count()>0:
<ul class="list-group">
% for m in page.media:
  <li class="list-group-item" data-toggle="tooltip" data-placement="left"
      data-html="true"
      title="<div style='background-color:white'><img style='max-height:50px;' src='{{m.preview_url}}'></div>">
      <span
      onclick="open_modal(global.base+'/page/'+global.page+'/get-media-templates/{{m.id}}')"
      title="Insert media into page at cursor" class="glyphicon glyphicon-circle-arrow-left media-selector"></span>
      <a href="#" title="Remove media from this page (does not delete from site)" onclick="delete_media({{m.id}})"><span class="pull-right glyphicon glyphicon-remove media-remove"></span></a>      
      <a target="_blank" href="{{settings.BASE_URL}}/blog/{{page.blog.id}}/media/{{m.id}}/edit">{{m.friendly_name}}</a>
  </li>
% end
</ul>
% end