<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:html="http://www.w3.org/1999/xhtml" xmlns:zero="http://arts.uwa.edu.au/els/zeroday" exclude-result-prefixes="html zero">
	<xsl:param name="poemindex" select="1"/>
	<xsl:template match="/">
		<xsl:for-each select="(//zero:poem)[position()=$poemindex]"><!-- >"> -->
		<div class="poem"><xsl:attribute name="id">poem<xsl:value-of select="$poemindex" /></xsl:attribute>
			<h1><xsl:value-of select="@title" />.</h1>
			<xsl:for-each select="zero:stanza"><div class="stanza">
				<xsl:for-each select="zero:line"><div class="line"><xsl:copy-of select="node()" /></div></xsl:for-each>
			</div></xsl:for-each>
		</div>
		</xsl:for-each>
	</xsl:template>
</xsl:stylesheet>