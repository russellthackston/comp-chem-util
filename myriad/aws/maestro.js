function parseResults(json)
{
	text = "";
	var jsonData = JSON.parse(json);
	for (var i = 0; i < jsonData.length; i++) {
		var result = jsonData[i];
		text += 
			result.job.JobName + "\t" + 
			result.job.JobGroup + "\t" + 
			result.JobCategory + "\t" + 
			result.job.JobDefinition.Displacements + "\t" + 
			result.JobResults + "\n";
	}
	document.getElementById("inputTextToSave").innerHTML = text;
}

function loadResults()
{
	var jobGroup = document.getElementById("jobGroup").value;
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			parseResults(this.responseText);
		}
	};
	xhttp.open("GET", "https://4rmyryq453.execute-api.us-east-1.amazonaws.com/prod?jobGroup=" + jobGroup, true);
	xhttp.send();
}

function saveTextAsFile()
{
	var textToSave = document.getElementById("inputTextToSave").value;
	var textToSaveAsBlob = new Blob([textToSave], {type:"text/plain"});
	var textToSaveAsURL = window.URL.createObjectURL(textToSaveAsBlob);
	var fileNameToSaveAs = document.getElementById("inputFileNameToSaveAs").value;

	var downloadLink = document.createElement("a");
	downloadLink.download = fileNameToSaveAs;
	downloadLink.innerHTML = "Download File";
	downloadLink.href = textToSaveAsURL;
	downloadLink.onclick = destroyClickedElement;
	downloadLink.style.display = "none";
	document.body.appendChild(downloadLink);

	downloadLink.click();
}
 
function destroyClickedElement(event)
{
	document.body.removeChild(event.target);
}

