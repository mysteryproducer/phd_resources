"use strict";
//There's no instance (this) context on the animation callback.
//Instead, add all the actors to a list.
const effectors=Array();

class TextEffect {
	constructor() {
		this.name="No effect";
	}
	getTotalFrames(allText) {
		return 1;
	}
	initialiseContainer(effector) {}
	initialiseElement(div) {}
	doFrameForward(timestamp,letterDivs) {}
	doFrameBackward(timestamp,letterDivs) {}
	elementComplete(node) {return true;}
}
class FadeEffect extends TextEffect {
	constructor(frameAlpha) {
		super();
		this.frameAlpha=0.2;
		this.name="Text Fade In"
		if (frameAlpha!=null && frameAlpha>0) {
			this.frameAlpha=frameAlpha;
		}
	}
	doFrameForward(ti1mestamp,letterDivs) {
		letterDivs.forEach(x=>
			x.style['opacity']=parseFloat(x.style['opacity'])+this.frameAlpha);		
	}
	elementComplete(node) {
		return parseFloat(node.style['opacity'])>=1;
	}
	initialiseContainer(effector) {
		let cnode=effector.contentDivs[0];
		let calpha=0;
		effector.letterDivs.forEach(div=>{
			cnode.insertBefore(div,cnode.invis);
			effector.grabText(div);
			div.style['opacity']=calpha;
			calpha -= 1/effector.letterDivs.length;
		});
	}
	initialiseElement(div) {
		div.style['opacity']=0;
	}
}

const degToRad=Math.PI/180;
class FlyInEffect extends TextEffect {
	constructor(angle,delay) {
		super();
		this.name="Text Fly In";
		this.angle=(angle==null)?0:angle;
		this.currentAngle=0;
		this.flies={};
		this.delay=(delay==null)?200:delay;
		this.pending=[];
		this.queue=[];
	}
	getTotalFrames(allText) {
		return 1;
	}
	getScreenPosition() {
		let angle=degToRad*(this.currentAngle%360);
		this.currentAngle+=this.angle;
		let win={hh:document.body.clientHeight/2,hw:document.body.clientWidth/2,x:document.body.scrollLeft,y:document.body.scrollTop};
		const radius=Math.sqrt(win.hh*win.hh+win.hw*win.hw);
		let x=(Math.sin(angle)* radius + win.hw + win.x);
		let y=Math.cos(angle)* radius + win.hh + win.y;
		return {left:x+'px',top:y+'px'}; 
	}
	initialiseContainer(effector) {
		let cnode=effector.contentDivs[0];
		this.flies={};
		let delay=0;
		//context for callbacks
		const me=this;
		const drain=[];
		let counter=0;
		let gap=this.delay/effector.letterDivs.length;
		effector.letterDivs.forEach(div=>{
			div.hashkey='d'+(counter++);
			cnode.insertBefore(div,cnode.invis);
			let fly=document.createElement('div');
			document.body.appendChild(fly);
			fly.style['position']='absolute';
			this.flies[div.hashkey]=fly;
			effector.grabText(div);
			fly.letter_div=div;
			fly.owner=this;
			fly.on_complete=()=>{
				//jquery documentation says 'this' is set to DOM element, but I'm getting the Effect instance.
				//Account for both:
				let x=(this.__proto__.constructor.name=='FlyInEffect')?this.queue.shift():this;
				x.letter_div.complete=true;
				$(x.letter_div).css({opacity:1});
				$(x).css({opacity:0});
			};
			drain.push(fly);
			delay+=gap;
			setTimeout(()=>me.pending.push(drain.shift()),delay);
		});
		this.pending=[];
	}
	initialiseElement(div,fly=null) {
		if (fly==null) {
			fly=this.flies[div.hashkey];
		}
		$(div).css({opacity:0});
		$(fly).css({opacity:1});
		$(fly).css(this.getScreenPosition());
		fly.innerHTML=div.innerHTML;
		div.complete=false;
		this.pending.push(fly);
	}
	doFrameForward(timestamp,letterDivs) {
		while(this.pending.length>0) {
			let div=this.pending.shift();
			this.queue.push(div);
			$(div).animate($(div.letter_div).offset(),this.delay,div.on_complete);
		};
	}
	doFrameBackward(timestamp,letterDivs) {

	}
	elementComplete(node) {
		return node.complete;
	}
}

class TextEffector {
	constructor(rootNode,letterCount,effect) {
		this.rootNode=rootNode;
		this.letterDivs=Array();
		for(let i=0;i<letterCount;++i) {
			this.letterDivs.push(document.createElement('span'));
		}
		this.contentDivs=this.getContent(this.rootNode);
		this.effect=effect;
		this.initialise();
	}
	start() {
		effectors.push(this);
	}
	makeCloseTags(tags) {
		let pos=0;
		let closeTags='';
		while (tags.indexOf('<',pos)>=0) {
			let ix=tags.indexOf('<',pos);
			let endTag=tags.indexOf('>',pos+1);
			let endType=tags.indexOf(' ',ix+1);
			closeTags+='</' + tags.substring(ix+1,Math.min(endTag,endType)) + '>';
			pos=ix+1;
		}
		return closeTags;
	}
	doFrame(timestamp) {
		this.effect.doFrameForward(timestamp,this.letterDivs);
		let last=this.letterDivs[0];
		if (this.effect.elementComplete(last)) {
			let pnode=last.parentNode;
			let content=last.innerHTML;
			let newTags='';
			let closeTags='';
			let oldVis=pnode.vis.innerHTML;
			if (content[0]=='<') {
				let endTag=content.indexOf('>');
				while (content[endTag+1]=='<') {
					endTag=content.indexOf('>',endTag+1);
				}
				let tags=content.substring(0,endTag+1);
				closeTags=this.makeCloseTags(tags);
				//todo: if an XML parser isn't involved, make sure this isn't a close tag
				if (pnode.vis.subnodestack.length==0) {
					newTags=tags;
				//if new tags added
				} else if (pnode.vis.subnodestack.length<tags.length) {
					newTags=tags.substring(pnode.vis.subnodestack.length);
					let oldCloseTags=this.makeCloseTags(pnode.vis.subnodestack);
					oldVis=oldVis.substring(0,oldVis.length-oldCloseTags.length);
				//if tags removed
				} else if (pnode.vis.subnodestack.length>tags.length) {
					let oldCloseTags=this.makeCloseTags(pnode.vis.subnodestack);
					oldVis=oldVis.substring(0,oldVis.length-closeTags.length);
				} else {
					//no change in tags
					newTags='';
					closeTags=this.makeCloseTags(pnode.vis.subnodestack);
					oldVis=oldVis.substring(0,oldVis.length-closeTags.length);
				}
				pnode.vis.subnodestack=tags;
				content=last.innerHTML.substring(tags.length,last.innerHTML.indexOf('<',tags.length));
			}
			pnode.vis.innerHTML=oldVis+newTags+content+closeTags;
			this.letterDivs.push(this.letterDivs.shift());
			pnode.removeChild(last);
			if (pnode.invis.remainderText.length==0) {
				//go to next div
				let ix=this.contentDivs.indexOf(pnode);
				for (;ix<this.contentDivs.length && this.contentDivs[ix].invis.remainderText.length==0;++ix) {}
				if (ix>=this.contentDivs.length) {
					this.letterDivs.pop();
					return;
				}
				pnode=this.contentDivs[ix];
			}
			pnode.insertBefore(last,pnode.invis);
			this.grabText(last);
			//last.style['opacity']=this.frameAlpha;
		}
	}
	grabText(node) {
		let pnode=node.parentNode;
		let remainder=pnode.invis.remainderText;
		if (remainder[0]=='<') {
			let endTagIndex=remainder.indexOf('>');
			if (remainder[1]=='/') {
				//I'm not checking that the close tag matches the open tag
				//because the content's been through an XML parser.
				pnode.invis.subnodestack.pop();
			} else {
				let tag=remainder.substring(0,endTagIndex+1);
				pnode.invis.subnodestack.push(tag);
			}
			remainder=remainder.substring(endTagIndex+1);
		}
		let prefix='';
		let suffix='';
		pnode.invis.subnodestack.forEach(x=>{
			prefix+=x;
			suffix='</' + x.substring(1,x.indexOf(' '))+'>'+suffix;
		});
		let rawText=remainder[0];
		if (rawText=='&') {
			rawText+=remainder.substring(1,remainder.indexOf(';')+1);
		}
		node.innerHTML=prefix+rawText+suffix;
		//problem?
		pnode.invis.remainderText=remainder.substring(rawText.length);
		pnode.invis.innerHTML=prefix+remainder.substring(rawText.length);
		this.effect.initialiseElement(node);
	}
	getContent(rootNode) {
		let allNodes=Array();
		allNodes.push(rootNode);
		let textnodes=Array();
		while (allNodes.length>0) {
			let hasText=false;
			let node=allNodes.shift();
			node.childNodes.forEach(snode=>{
				if (snode.nodeType==3) {hasText=true;}
			});
			if (hasText) {
				textnodes.push(node);
			} else {
				node.childNodes.forEach(x=>allNodes.push(x));
			}
		}
		//drop the title node
		textnodes.shift();
		return textnodes;
	}
	initialise() {
		this.contentDivs.forEach(div=>{
			let contents=div.innerHTML;
			div.innerHTML='';
			let nn=document.createElement('span');
			nn.subnodestack='';
			div.appendChild(nn);
			div.vis=nn;

			nn=document.createElement('span');
			nn.style['opacity']=0;
			nn.subnodestack=[];
			div.appendChild(nn);
			div.invis=nn;
			div.invis.remainderText=contents;
			div.invis.innerHTML=contents;
		});
		//init fader divs. TODO: presumes node has >n chars in its text
		this.effect.initialiseContainer(this);
	}
	stop() {
		effectors.splice(effectors.indexOf(this),1);
	}
}
function doFrame(timestamp) {
	effectors.forEach(x=>x.doFrame(timestamp));
	requestAnimationFrame(doFrame);
}
requestAnimationFrame(doFrame);
function slide_go(nodeID) {
	const fader=new TextEffector(document.getElementById(nodeID),20,new FlyInEffect(7,1000));
	fader.start();
	return fader;
}
function fader_go(nodeID) {
	const fader=new TextEffector(document.getElementById(nodeID),20,new FadeEffect(0.05));
//	const fader=new TextEffector(document.getElementById(nodeID),20,new FlyInEffect(-1,2000));
	fader.start();
	return fader;
}
