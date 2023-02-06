"use strict";

class MagneticField {
	constructor(rootNode) {
		this.rootNode=rootNode;
		this.wordDivs=Array();
		//add big field div
		this.field=document.createElement('div');
		document.body.appendChild(this.field);
		$(this.field).addClass('field');
		$(this.field).css({width:'300vw',height:'300vh'});
		$(this.rootNode).css({position:'fixed'});
		let contentDivs=this.getContent(this.rootNode);
		this.initialise(contentDivs);
	}
	getContent(rootNode) {
		let allNodes=Array();
		allNodes.push(rootNode);
		let textnodes=Array();
		while (allNodes.length>0) {
			allNodes.shift().childNodes.forEach(node=>{
				if (node.nodeType==3) {
					textnodes.push(node.parentNode);
				}
				node.childNodes.forEach(x=>allNodes.push(x));
			});
		}
		return textnodes;
	}
	initialise(contentDivs) {
		contentDivs.forEach(div=>{
			div.innerHTML='<span class=\"original word\">' + div.innerText.replaceAll(' ','</span> <span class=\"original word\">') + '</span>';
			let words=div.getElementsByClassName('word');
			for(let i=0;i<words.length;++i) {
				let ws=words[i];
				let mag=document.createElement('div');
				mag.innerText=ws.innerText;
				mag.home=ws;
				this.field.appendChild(mag);
				$(mag).addClass(['floating','word']);
				$(mag).css({top:Math.random()*200+'vw',left:Math.random()*250+'vh'});
				$(ws).css({opacity:0});
			}
		});
	}
}
function distance(a,b) {
	return Math.sqrt(Math.pow(a.left-b.left,2)+Math.pow(a.top-b.top,2));
}
const float_hooked=[];
let timeHandle=null;
let tree=null;
function refreshAnimation(){
	float_hooked.forEach(x=>{
		let dest=$(x.home).offset();
		$(x).stop();
		$(x).animate(dest,1000,()=>{
			if (timeHandle==null) {
				x.remove();
				$(x.home).css({opacity:1});
				let d_ix=float_hooked.indexOf(x);
				while (d_ix>=0) {
					float_hooked.splice(d_ix,1);
					d_ix=float_hooked.indexOf(x);
				}
			}
		});
	});
	timeHandle=null;
}
function magnet_go(nodeID) {
	const rootNode=document.getElementById(nodeID);
	const mf_doom=new MagneticField(rootNode);
	let fds=mf_doom.field.getElementsByClassName('floating');
	let floats=[]
	for (let i=0;i<fds.length;++i) {
		let flt=$(fds[i]).offset();
		flt.div=fds[i];
		floats.push(flt);
	}
	tree=new kdTree(floats,distance,['left','top']);
	$(window).scroll(()=>{
		let centre={
			left:document.body.scrollLeft + rootNode.clientWidth/2,
			top:document.body.scrollTop + rootNode.clientHeight/2
		};
		let popped=tree.nearest(centre, 200, Math.max(rootNode.clientWidth,rootNode.clientHeight));
		popped.forEach(x=>{
			let xd=x[0].div;
			float_hooked.push(xd);
			tree.remove(x);
		});
		if (timeHandle!=null) {
			clearTimeout(timeHandle);
		}
		timeHandle=setTimeout(refreshAnimation,10);
	});
}
	