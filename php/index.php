<?php
session_start();
$background_img=get_wash();
$dark_mode=basename($background_img)[0]=='0';
7?>
<html>
<head>
	<title>Zero Day</title>
	<link rel="icon" type="image/x-icon" href="favicon.ico">
	<link rel="preload" href="css/fonts/Karma/Karma-Regular.ttf" as="font">
	<link rel="preload" href="css/fonts/Impact/Impact.woff" as="font">
	<style>
		@font-face {font-family: 'karma';src: url('css/fonts/Karma/Karma-Regular.ttf') format('truetype'),url('css/fonts/Karma/Karma-Regular.woff') format('woff');}
		@font-face {font-family: 'impact';src: url('css/fonts/Impact/Impact.ttf') format('truetype'),url('css/fonts/Impact/Impact.woff') format('woff');}
		:root {
			--back:<?php echo $dark_mode?"black":"white" ?>;
			--fore:<?php echo $dark_mode?"white":"black" ?>;
			--backimage:url("<?php echo '../' . $background_img; ?>")
		}
	</style>
	<link rel="stylesheet" href="css/zeroday.css"/>
	<link rel="stylesheet" href="css/parallax.css"/>
	<script src="js/jquery-3.6.1.min.js"></script>
	<script src="js/kdTree-min.js"></script>
	<script src="js/fader2.js"></script>
	<script src="js/magnet.js"></script>
</head>
<body>
	<div class="factsheet"><a href="karma_infosheet.pdf">KARMA attack information sheet—click here</a></div>
<?php
$vmac=getClientMAC();
$tracker=new DivergentReader($vmac);

$xml = new DOMDocument();
$xml->load('xml/poems.xml');
$xsl = new DOMDocument();
$xsl->load('xml/poems.xslt');
$f1=function($n){renderNormal($n);};
$f2=function($n){renderParallax($n);};
$f3=function($n){renderAlpha($n);};
$f4=function($n){renderDrip($n);};
$f5=function($n){renderMagnetic($n);};
$render_types=[$f2,$f3,$f4,$f5];

$zprefix=$xml->lookupPrefix('http://arts.uwa.edu.au/els/zeroday');
$all_poems=$xml->getElementsByTagNameNS('http://arts.uwa.edu.au/els/zeroday', 'poem');
$ix=$tracker->getOffset($all_poems->count());
emit($xml,$ix,$xsl,$render_types);

function emit($xml,$index,$xsl,$functions) {
	//$index=6;
	// Configure the transformer
	$proc = new XSLTProcessor();
	$proc->importStyleSheet($xsl); // attach the xsl rules
	$proc->setParameter('','poemindex',strval($index));

	$tx=$proc->transformToDoc($xml);
	$functions[$index%4]($tx);
}
function get_wash() {
	return get_rand_image('img/wash');
}
function join_paths() {
    $paths = array();
    foreach (func_get_args() as $arg) {
        if ($arg !== '') { $paths[] = $arg; }
    }
    return preg_replace('#/+#','/',join('/', $paths));
}
function get_rand_image($rel_path='img',$types='*.jpg') {
	$searchpath=join_paths(pathinfo($_SERVER['SCRIPT_FILENAME'])['dirname'],$rel_path,$types);
	$files=glob($searchpath);
	$ifile=$files[rand(0,count($files)-1)];
	return join_paths($rel_path,basename($ifile));
}

function nodeToText($xml,$node) {
	$content=($node==null)?$xml->saveHTML():$xml->saveHTML($node);
	$content=str_replace(' xmlns=""','',$content);
	$content=str_replace(' xmlns="http://www.w3.org/1999/xhtml"','',$content);
	return $content;
}

function renderParallax($xml) {
	$elements=$xml->getElementsByTagName('div');
	echo('<div class="poem parallax">');
	echo('<div class="parallaxTitle">' . nodeToText($xml,$xml->getElementsByTagName('h1')[0]) . '</div>');
	$i=0;
	$suffixes=['base','back','deep'];
	$groupnum=0;
	$img_layer=2;
	foreach ($elements as $node) {
		if ($node->attributes['class']->value=='stanza') {
			if($i==0) {
				if ($groupnum!=0) {echo '</div>';}
				echo '<div id="group' . $groupnum . '" class="parallax__group">';
				$groupnum+=1;
			}
			echo '<div class="parallax__layer ' . $suffixes[$i] . '">';
			echo '<div>' . nodeToText($xml,$node) . '</div>';
			echo '</div>';
			if($i==1) {
				echo '<div class="parallax__layer deep">';
				echo '<div class="img_div" style="background-image:url(\'' . get_rand_image() . '\');"></div>';
				echo '</div>';
			}
			$i=($i+1)%2;
		}
	}
	if($i>0) {
		echo '<div class="parallax__layer deep"><div class="img_div" style="background-image:url(\'' . get_rand_image() . '\');"></div></div>';
	}
	echo('</div></div>');
}

function renderScripted($xml,$jsfn,$extra=null) {
	$topNode=$xml->documentElement;
	echo nodeToText($xml,$topNode);
	$nodeID=$topNode->attributes[1]->textContent;
	$script='<script>$(document).ready(function() {' . $jsfn . '(\'' . $nodeID . '\');});' . $extra . '</script>';
	echo $script;
}

function addImage() {
	echo('<div style="position:absolute;z-index:-1;top:60vh;left:70vw"><img style="max-width:20vw" src="' . get_rand_image() . '"></img></div>');
}

function renderAlpha($xml) {
	renderScripted($xml,'fader_go');
	addImage();
}
function renderDrip($xml) {
	renderScripted($xml,'slide_go',
	'
	$(window).ready(function(){
		$(document.body).css({overflow:\'hidden\'});
		$(\'.poem\').css({overflow:\'auto\',maxHeight:\'100vh\',maxWidth:\'100vw\'});
	});');
	addImage();
}
function renderMagnetic($xml) {
	renderScripted($xml,'magnet_go');
	for ($i=0;$i<5;++$i) {
		$randomPos=sprintf('left: %uvw;top: %uvh',random_int(0,200),random_int(0,200));
		echo('<div style="position:absolute;z-index:1;' . $randomPos . '"><img style="max-width:100vw" src="' . get_rand_image() . '"></img></div>');
	}
}
function renderNormal($xml) {
	echo nodeToText($xml,null);
}

//Client/victim management
function getClientMAC() {
	//get the MAC if passed from wifiphisher
    $allHdrs=getallheaders();
    foreach($allHdrs as $k=>$v) {
        if (strtolower($k)=="x-client-mac") {
            return $v;
        }
    }
	//else use session id as unique key
    return session_id();
}
class DivergentReader {
	//could do this with a database; it'd get rid of all this nasty with the file handling.
	//Doesn't seem worth it, and working out of a RAMdisk would make that difficult
	const FILENAME="/run/zeroday/mac_register.txt";
	const BLOCK_SIZE=120; //in seconds
	const MAX_AGE=3600; // in seconds
	private $newSesh;
	private $readerOffset;
	function __construct($clientMAC) {
		touch(self::FILENAME);
		$file=fopen(self::FILENAME,"rw+");
		$block=1;
		//The top row has the most recently assigned offset.
		//In effect: go through the whole file. Look for this client's record. While you're there, scrub any old ones.
		//Replace the file when done.
		if (flock($file,LOCK_EX,$block)) {
			$this->newSesh=true;
			$records=explode("\r\n",file_get_contents(self::FILENAME));
			$mostRecentOffset=intval(array_shift($records));
			$newRecords=array();
			foreach ($records as $record) {
				$items=explode("|",$record);
				//format, each line: MAC Address|Session Last Accessed|Reader Offset
				$age=intval($items[1]);
				$offset=intval($items[2]);
				if (strcmp($clientMAC,$items[0])==0) {
					$this->newSesh=false;
					$this->readerOffset=$offset;
					array_push($newRecords,$clientMAC.'|'.time().'|'.$offset);
				//expire records by not copying them to output
				} else if (time()-$age<self::MAX_AGE) {
					array_push($newRecords,$record);
				}
			}
			if ($this->newSesh) {
				$mostRecentOffset=(count($newRecords)==0)?0:$mostRecentOffset+1;
				$this->readerOffset=$mostRecentOffset;
				array_push($newRecords,$clientMAC.'|'.time().'|'.$this->readerOffset);
			}
			array_splice($newRecords,0,0,[sprintf('%u',$mostRecentOffset)]);
			file_put_contents(self::FILENAME,join("\r\n",$newRecords));
			flock($file,LOCK_UN);
		}
	}
	public function isNewSession() {
		return $this->newSesh;
	}
	public function getIndex($arraySize) {
		$bigix=floor(time()/self::BLOCK_SIZE) + $this->readerOffset;
		return $bigix % $arraySize + 1;
	}
}
?>
</body>
</html>
