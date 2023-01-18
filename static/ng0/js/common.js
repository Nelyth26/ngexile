function $(element) { return document.getElementById(element) }

function donothide(event) {
    
    event.cancelBubble = true
    return false
}

function getval(name) {
    
	let obj = document.getElementsByName(name)
	if (obj != null) obj = obj[0]
	if (obj == null) obj = document.getElementById(name)
        
	if (obj == null) return 0

	let s = parseInt(obj.value, 10)
	if(isNaN(s) || (s < 0)) return 0
    else return s
}

function setval(name, val) {
    
	let obj = document.getElementsByName(name)
	if (obj != null) obj = obj[0]
	if (obj == null) obj = document.getElementById(name)
    
	obj.value = val
}

function evalResponse(req) {
    
    if (req.status == '200') eval(req.responseText)
    else window.location.reload(true)
}

/* Hide/Show div boxes */

let showidx = 0
let lastobjref = ''
let lastobjrefcontent = ''

function hide() {
    
	if (lastobjref != '') {
        
		$(lastobjref).innerHTML = lastobjrefcontent
		lastobjref = ''
	}
}

function show(objref, objbox) {
    
	hide()
    
	let objr = $(objref)
	let objb = $(objbox)

	lastobjref = objref
	lastobjrefcontent = objr.innerHTML

	objr.innerHTML = objb.innerHTML.replace(/XXX/g, showidx)

	showidx++

	return false
}

/* Functions */

let wbr = '<wbr/>'
if (navigator.userAgent.indexOf('Opera') != -1) wbr = '&#8203;'

function addWbr(str) {
    
	if (str.length < 30) return str

	let s = ''
	for (let k = 0; k < str.length; k += 2) s = s + str.substr(k, 2) + wbr
    
	return s
}

function addThousands(nStr, outD, sep) {
    
	nStr += ''
	let dpos = nStr.indexOf('.')
	let nStrEnd = ''
	if (dpos != -1) {
        
		nStrEnd = outD + nStr.substring(dpos + 1, nStr.length);
		nStr = nStr.substring(0, dpos);
	}
    
	let rgx = /(\d+)(\d{3})/
	while (rgx.test(nStr)) nStr = nStr.replace(rgx, '$1' + sep + '$2')
    
	return nStr + nStrEnd
}

function formatnumber(n) { return addThousands(n, '.', ' ') }

/* Planet */

function planet_str(id, name, g, s, p, rel) {
    
    switch (rel) {
        
        case 2: var col = 'link-info'; break;
        case 1: var col = 'link-success'; break;
        case 0:	var col = 'link-success'; break;
        case -1: var col = 'link-danger'; break;
        case -2: var col = 'link-danger'; break;
        case -3: var col = 'link-normal'; break;
    }

    return '<a href="/ng0/map/?g=' + g + '&s=' + s + '" class="' + col + '"><i class="fa-fw fas fa-map"></i> ' + g + '.' + s + '.' + p + '</a>'
}

function putplanet(id, name, g, s, p, rel) { document.write(planet_str(id, name, g, s, p, rel)) }
