function refresh() {
        var xhttp = new XMLHttpRequest({mozSystem: true});
        xhttp.onreadystatechange = function() {
                if (xhttp.readyState == 4 && xhttp.status == 200) {
                        let results = JSON.parse(xhttp.responseText);
                        jobsTable = document.getElementById("jobs")
                        headerrow = jobsTable.rows[0].innerHTML;
                        jobsTable.innerHTML = "";
                        jobsTable.insertRow(0).innerHTML = headerrow;
                        for(var i=0;i<results.length;i++){
                                var item = results[i];
                                // {"LastUpdate": "2016-06-30 12:53:54","ExecutionFailed": "0","JobResults": "0E-16",
                                // "Created": "2016-06-29 22:22:39","MachineID": "0.0.0.0","ResultsCollected": "2016-06-30 12:53:54",
                                // "MakeInputDatParameters": "TZ","JobStarted": "2016-06-30 12:53:54","JobStatus": "Placeholder",
                                // "JobID": "1","ExecutionID": "159","JobGUID": "0","JobGroup": "SNS_PI",
                                // "JobDefinition": "-1,-2,0,0","JobName": "SNS_PI_TZ-1","JobResultsID": "159"}
                                var rowCount = jobsTable.rows.length;
        			var row = jobsTable.insertRow(rowCount);
        			row.className = item['JobStatus'];
        			var cell = row.insertCell(0).innerHTML = item['JobStatus'];
        			var cell = row.insertCell(1).innerHTML = item['JobID'];
        			var cell = row.insertCell(2).innerHTML = item['JobName'];
        			var cell = row.insertCell(3).innerHTML = item['JobGroup'];
        			var cell = row.insertCell(4).innerHTML = item['JobStarted'];
        			var cell = row.insertCell(5).innerHTML = item['JobDefinition'];
        			var cell = row.insertCell(6).innerHTML = item['MakeInputDatParameters'];
        			var cell = row.insertCell(7).innerHTML = item['LastUpdate'];
        			var cell = row.insertCell(8).innerHTML = item['ExecutionFailed'];
        			var cell = row.insertCell(9).innerHTML = item['JobResults'];
        			var cell = row.insertCell(10).innerHTML = item['MachineID'];
        			var cell = row.insertCell(11).innerHTML = item['ResultsCollected'];
        			var cell = row.insertCell(12).innerHTML = item['JobResultsID'];
        			var cell = row.insertCell(13).innerHTML = item['ExecutionID'];
        			var cell = row.insertCell(14).innerHTML = item['JobGUID'];
                        }
                }
        };
        xhttp.open("GET", "https://4rmyryq453.execute-api.us-east-1.amazonaws.com/prod", true);
        xhttp.send();
}

function refreshTable() {
        var xhttp = new XMLHttpRequest({mozSystem: true});
        xhttp.onreadystatechange = function() {
                if (xhttp.readyState == 4 && xhttp.status == 200) {
                        let results = JSON.parse(xhttp.responseText);
                        jobsTable = document.getElementById("jobs")
                        jobsTable.innerHTML = "";
                        var rows = Math.ceil(Math.sqrt(results.length));
                        var cols = Math.ceil(results.length / rows);
                        var c = 0;
                        var row = null;
                        for(var i=0;i<results.length;i++){
                                var item = results[i];
                                if (c == 0) {
                                        var rowCount = jobsTable.rows.length;
                                        row = jobsTable.insertRow(rowCount);
                                }
                                var j = encodeURI(JSON.stringify(item));
        			var cell = row.insertCell(c).innerHTML = "<div class='"+item['JobStatus']+"'><a href='d.html?j="+j+"' target='_blank'>" +item['JobID'] + "</a></div>";
        			
                                c++;
                                if (c > cols) {
                                        c = 0;
                                }
                        }
                }
        };
        xhttp.open("GET", "https://4rmyryq453.execute-api.us-east-1.amazonaws.com/prod", true);
        xhttp.send();
}

function showDetails() {
        tmp = decodeURI(location.search.substring(3));
        items = JSON.parse(tmp);

        jobsTable = document.getElementById("jobs");
        // {"LastUpdate": "2016-06-30 12:53:54","ExecutionFailed": "0","JobResults": "0E-16",
        // "Created": "2016-06-29 22:22:39","MachineID": "0.0.0.0","ResultsCollected": "2016-06-30 12:53:54",
        // "MakeInputDatParameters": "TZ","JobStarted": "2016-06-30 12:53:54","JobStatus": "Placeholder",
        // "JobID": "1","ExecutionID": "159","JobGUID": "0","JobGroup": "SNS_PI",
        // "JobDefinition": "-1,-2,0,0","JobName": "SNS_PI_TZ-1","JobResultsID": "159"}
        fields = ['JobStatus','JobID','JobName','JobGroup','JobStarted','JobDefinition',
                'MakeInputDatParameters','LastUpdate','ExecutionFailed',
                'JobResults','MachineID','ResultsCollected','JobResultsID','ExecutionID','JobGUID'];
        for (var i=0;i<fields.length;i++){
                var field = fields[i];
                var value = items[field];
                addRow(field, value);
        }
}

function addRow(field, value) {
        var row = jobsTable.insertRow(jobsTable.rows.length);
        var cell = row.insertCell(0);
        cell.innerHTML = field;
        row.insertCell(1).innerHTML = value;
}