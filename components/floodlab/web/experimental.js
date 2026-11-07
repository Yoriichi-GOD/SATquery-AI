'use strict';
const originalTab=tab;
tab=function(evaluation){$('#experiment').hidden=true;$('#experiment-tab').classList.remove('active');originalTab(evaluation)};
$('#experiment-tab').onclick=()=>{$('#lab').hidden=true;$('#evaluation').hidden=true;$('#experiment').hidden=false;$('#lab-tab').classList.remove('active');$('#eval-tab').classList.remove('active');$('#experiment-tab').classList.add('active')};
$('#run').disabled=true;$('#run').title='Original analysis specialists are not connected to this isolated experimental backend.';
const boundary=document.querySelector('.boundary');boundary.replaceChildren(element('b','Experimental workspace · local only'),element('p','The SatQuery interface is copied here. Original analysis specialists are not connected yet. Open Experimental for the tested flood pipeline and Evidence for this application’s verification results.'));
if(location.hash==='#evidence')tab(true);else if(location.hash==='#experimental')$('#experiment-tab').click();
