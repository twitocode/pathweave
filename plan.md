Okay, so the goal is to change sc our data scraping method for schedules. Instead of looking at my timetable, which is a bit finicky, we could we could instead just go to Mosaic for McMaster as it has more up to date information but it is a bit harder to navigate. PUT THIS IN A SEPARATE FILE here are the steps:

go to https://mosaic.mcmaster.ca/psp/prcsprd/?cmd=login
login with MOSAIC_USERNAME and MOSAIC_PASSWORD which are already set in .env
password field is input id "pwd"
macid field is input id "userid"

then submit the form with id "login"

there should then be a div with id="win0divPTNUI_LAND_REC_GROUPLET$8" that will take you to the student center
next press the a tag with id="DERIVED_SSS_SCR_SSS_LINK_ANCHOR1". this will take you to the course search page

Next press this a tag: <a href="/psc/prcsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL?Page=SSS_BROWSE_CATLG&amp;Action=U" onclick="ShowLoading()" class="PSHYPERLINK" tabindex="22" accesskey="B"><span style="font-size:11px; white-space: nowrap;"><abbr onclick="ShowLoading()" class="PTUNDERLINE">B</abbr>rowse Course Catalog</span></a>
This will take you to the course catalog.

This select box will have the option "Undergradute" as the option: <select name="MCM_SSS_BCC_WRK_ACAD_CAREER" id="MCM_SSS_BCC_WRK_ACAD_CAREER" tabindex="31" size="1" class="PSDROPDOWNLIST" style="width:197px; " fn="ACAD_CAREER" onchange="addchg_win0(this);submitAction_win0(this.form,this.id);" onkeydown="if ((typeof isLoaderInProcess == 'function') &amp;&amp; isLoaderInProcess() &amp;&amp; ptCommonObj2!=null) { ptCommonObj2.terminateEvent(event); } ">

<option value="" selected="selected">&nbsp; </option>
<option value="CCE">Continuing Education</option>
<option value="DIV">Divinity College</option>
<option value="GRAD">Graduate</option>
<option value="IND">Independent</option>
<option value="MED">Medicine</option>
<option value="UGRD">Undergraduate</option>
</select>

Then under it will be the term selection option. For the term choose 2026 Fall, 2027 Winter and 2027 Spring/Summer for different runs, make sure i can easily change it in the code
<select name="MCM_SSS_BCC_WRK_STRM" id="MCM_SSS_BCC_WRK_STRM" tabindex="32" size="1" class="PSDROPDOWNLIST" style="width:199px; " fn="STRM" onchange="addchg_win0(this);return doEdits_win0(this,'','N','N','N','N','Y','Y',0);" onkeydown="if ((typeof isLoaderInProcess == 'function') &amp;&amp; isLoaderInProcess() &amp;&amp; ptCommonObj2!=null) { ptCommonObj2.terminateEvent(event); } ">

<option value="2259" selected="selected">						2025 Fall</option>
<option value="2261">					2026 Winter</option>
<option value="2265">				2026 Spring/Summer</option>
<option value="2269">			2026 Fall</option>
<option value="2271">		2027 Winter</option>
<option value="2275">	2027 Spring/Summer</option>
<option value="">&nbsp; </option>
</select>

Then you will press this input to search: <input type="button" name="MCM_SSS_BCC_WRK_SSS_PB_CHANGE" id="MCM_SSS_BCC_WRK_SSS_PB_CHANGE" tabindex="33" value="Search" class="PSPUSHBUTTON" style="width:98px; " onclick="submitAction_win0(document.win0,this.id,event);" title="Change Institution / Career">

Then after a bit it will pull up the results.

There should be an "Expand All" button that expands all the results to show each course:

<div id="win0divDERIVED_SSS_BCC_SSS_EXPAND_ALL$97$"><a role="presentation" class="PSPUSHBUTTON Left"><span style="background-Color: transparent;"><input type="button" name="DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$" id="DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$" tabindex="105" value="Expand All" class="PSPUSHBUTTON" style="width:128px; " onclick="submitAction_win0(document.win0,this.id,event);" title="Expand All Sections"></span></a></div>

Then the courses will be expanded and you will see multiple tables with course nbr and course title

Each entry looks like this:
<tr id="trCOURSE_LIST$1_row1" bufnum="0" valign="center" onclick="HighLightTR('rgb(238,238,238)','','trCOURSE_LIST$1_row1');" onmouseover="hoverLightTR('rgb(253,255,200)','',0,'trCOURSE_LIST$1_row1');" onmouseout="hoverLightTR('rgb(253,255,200)','',1,'trCOURSE_LIST$1_row1');">
<td align="CENTER" style="white-space: nowrap;" height="20" class="PSLEVEL2GRIDODDROW PSGRIDFIRSTCOLUMN">
<div id="win0divCRSE_SEL_CHECKBOX$0"><input type="hidden" name="CRSE_SEL_CHECKBOX$chk$0" id="CRSE_SEL_CHECKBOX$chk$0" value="N">
<input type="checkbox" name="CRSE_SEL_CHECKBOX$0" id="CRSE_SEL_CHECKBOX$0" class="PSCHECKBOX" tabindex="319" value="Y" onclick="setupTimeout2();    this.form.CRSE_SEL_CHECKBOX$chk$0.value=(this.checked?'Y':'N');doFocus_win0(this,false,true);">
</div></td>
<td class="PSLEVEL2GRIDODDROW" align="CENTER" style="">
<div id="win0divCRSE_NBR$0"><span id="CRSE_NBR$span$0" class="PSHYPERLINK"><a name="CRSE_NBR$0" id="CRSE_NBR$0" ptlinktgt="pt_peoplecode" tabindex="320" onclick="javascript:cancelBubble(event);" href="javascript:submitAction_win0(document.win0,'CRSE_NBR$0');" class="PSHYPERLINK">   2PA6</a></span></div></td>
<td class="PSLEVEL2GRIDODDROW" align="left" style="">
<div id="win0divCRSE_TITLE$0"><span id="CRSE_TITLE$span$0" class="PSHYPERLINK" title="Course Title"><a name="CRSE_TITLE$0" id="CRSE_TITLE$0" ptlinktgt="pt_peoplecode" tabindex="321" onclick="javascript:cancelBubble(event);" href="javascript:submitAction_win0(document.win0,'CRSE_TITLE$0');" class="PSHYPERLINK">Making an Impact: Building Skills and Relationships for Collaborative Social Change</a></span></div></td>
<td class="PSLEVEL2GRIDODDROW" align="left" style="">
<div id="win0divCRSE_TYPOFF$0"><span class="PSEDITBOX_DISPONLY" id="CRSE_TYPOFF$0">&nbsp;</span>
</div></td>
</tr>

within the row i want you to click the a tag with id="CRSE_TITLE$0". replace 0 with the row number starting from 0, tables in other rows should continue the same numbering as in table 1 is 0-10, table 2 is 11-20, etc.

Some courses will say "This course has not been scheduled." in that case just set the schedules to be empty. this probably means that it is available in another term.
But most will have this a tag <a role="presentation" class="PSPUSHBUTTON Left"><span style="background-Color: transparent;"><input type="button" name="DERIVED_SAA_CRS_SSR_PB_GO" id="DERIVED_SAA_CRS_SSR_PB_GO" tabindex="96" value="View Class Sections" class="PSPUSHBUTTON" style="width:195px; " onclick="submitAction_win0(document.win0,this.id,event);"></span></a>. Then after a bit it will show all of the course schedules

Here is a structured breakdown of the elements in this layout to make it highly digestible for your scraping tool.

The document is structured as a series of repeating tables containing metadata about sections, where each schedule block has a clear parent-child relationship.

---

## 1. Targeting the Course and Rows

The table container for the entire list of sections can be found via:

```css
table[id^="CLASS_TBL_VW5$scroll"]

```

Inside this container, each section is broken down into consecutive rows or sub-tables inside the main container body.

---

## 2. Scraping the Section Header (Parent Row)

To grab each individual section's core information (Name, Session, Status), look for the main section table rows:

* **Target:** `tr[id^="trCLASS$"]`

Inside this table row, the properties are mapped as follows:

| Field | Selector / Logic | Example Value |
| --- | --- | --- |
| **Section Name & ID** | `span[id^="CLASS_SECTION$span"] a` | `C01-LEC (3042)` |
| **Session** | `span[id^="CLASS_SESSION$"]` | `1` |
| **Status** | Find the `img` element inside `div[id^="win0divCLASS_STATUS$"]` and extract the `alt` attribute. | `Open` |

---

## 3. Scraping Section Details (Child Rows)

Directly following or associated with each section header row is a "Section Details" block. This holds the actual times, days, and locations.

* **Target Container:** `table[id^="CLASS_MTGPAT$scroll"]`
* **Target Rows:** `tr[id^="trCLASS_MTGPAT$"]`

*Note: Some sections have multiple schedule rows (e.g., L01-LAB has 2 rows, L04-LAB has 4 rows). You should loop through all matching rows inside this container block.*

Inside each detail row, extract the data using these specific `id` attributes or partial matches:

| Field | Selector / Logic | Example Value |
| --- | --- | --- |
| **Days** | `span[id^="MTGPAT_DAYS$"]` | `MoWe` |
| **Start Time** | `span[id^="MTGPAT_START$"]` | `5:30PM` |
| **End Time** | `span[id^="MTGPAT_END$"]` | `6:20PM` |
| **Room / Mode** | `span[id^="MTGPAT_ROOM$"]` | `PGCLL B138` or `In Person` |
| **Instructor** | `span[id^="MTGPAT_INSTR$"]` | `Samuel Scott` |
| **Date Range** | `span[id^="MTGPAT_DATES$"]` | `05/01/2026 - 07/04/2026` |

---

## 4. Traversal Logic Tip for the Parser

Because PeopleSoft renders these as independent nested blocks divided by `<hr>` tags (`hr.PAHORIZONTALRULELEVEL1`), the cleanest approach for your script is:

1. Locate all section tables (`div[id^="win0divCLASS$"]`).
2. For each section, extract the title and status.
3. Find the immediate next sibling container for details (`div[id^="win0divCLASS_MTGPAT$"]`).
4. Loop through every `tr` inside that container's `tbody` to map the arrays of locations, rooms, and times to that specific section.

then log out the data collected.

AFTER EITHER SCRAPING THE DATA OR DATA COULD NOT BE FOUND
press the close button that should look like this: <a class="PSMODALCLOSEANCHOR" style="border:none;padding:0px;margin:0px;text-decoration:none;" title="Close" id="ptModCloseLnk_18" href="javascript:doCloseModal(18);"></a>
It should wait roughly 1 second before going on to the next course so that it can let mosaic do its thing

then go to the next course