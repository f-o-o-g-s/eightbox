"""Documentation content for Article 8 violations."""

DOCUMENTATION_85D = """
<h2 style='color: #BB86FC; font-size: 24px; margin: 20px 0;'>
    Article 8.5.D - Overtime Off Assignment
</h2>

<h3 style='color: #03DAC6; font-size: 20px; margin: 16px 0;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 15px; border-radius: 4px; font-size: 16px; line-height: 1.6;'>
    "<strong style='color: #BB86FC;'>If the voluntary 'Overtime Desired' list does not provide sufficient qualified people</strong>, "
    "qualified full-time regular employees not on the list may be required to work overtime "
    "on a rotating basis with the first opportunity assigned to the junior employee."
</p>
<p style='font-style: italic; color: #03DAC6; margin-top: 10px; font-size: 14px;'>
    Note: This language establishes a crucial requirement - management must first attempt to use all available OTDL carriers 
    to their maximum daily (12 hours) and weekly (60 hours) limits before requiring WAL or NL carriers to work overtime off 
    their assignment. This is why checking if the OTDL was maximized is a key condition for violations.
</p>
<p style='font-style: italic; color: #03DAC6; margin-top: 10px; font-size: 14px;'>
    Display Indicator: When a violation occurs on a carrier's non-scheduled day, you will see "(NS day)" next to the remedy amount. 
    This indicates that the carrier is entitled to the full day's hours as remedy, rather than just the overtime portion.
</p>

<h3 style='color: #03DAC6; font-size: 20px; margin: 16px 0;'>When Does a Violation Occur?</h3>
<p style='font-size: 16px; line-height: 1.6;'>A violation occurs when ALL of these conditions are met:</p>
<ul style='font-size: 16px; line-height: 1.8; margin-left: 20px;'>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The carrier worked overtime off their assignment (either their regular route or T6 string)</li>
    <li>The Overtime Desired List (OTDL) was not maximized that day</li>
</ul>

<h3 style='color: #03DAC6; font-size: 20px; margin: 16px 0;'>How is the Remedy Calculated?</h3>
<p>The remedy calculation depends on whether it's a regularly scheduled day or non-scheduled day:</p>

<h4 style='color: #BB86FC; margin: 16px 0;'>On a Regularly Scheduled Day:</h4>
<ol>
    <li>First, calculate how many overtime hours were worked:
        <br>• Take the total hours worked that day
        <br>• Subtract 8 hours (regular work day)
        <br>• This gives you the overtime hours
    </li>
    <li>Next, determine how many hours were worked off assignment:
        <br>• Add up all the time spent working routes other than their own
        <br>• This gives you the off-assignment hours
    </li>
    <li>The remedy will be the smaller of these two numbers:
        <br>• If they worked more hours off assignment than overtime hours, the remedy is the overtime hours
        <br>• If they worked more overtime hours than off assignment hours, the remedy is the off-assignment hours
    </li>
</ol>

<h4 style='color: #BB86FC; margin: 16px 0;'>On a Non-Scheduled Day:</h4>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    When a carrier works on their non-scheduled day:
    <br>• ALL hours worked that day are considered off-assignment
    <br>• The remedy is equal to the total hours worked that day
    <br>• The display will show "(NS day)" to indicate this special case
</p>

<h3 style='color: #03DAC6; font-size: 20px; margin: 16px 0;'>Examples:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                <strong>Regular Day Example:</strong>
                <br>
                A WAL carrier has:
                <br>
                • Total hours worked: 10 hours
                <br>
                • Hours on other routes: 3 hours
                <br><br>
                Remedy Calculation:
                <br>
                • Overtime hours = 10 - 8 = 2 hours
                <br>
                • Hours off assignment = 3 hours
                <br>
                • Remedy = 2.00 hours
            </p>
        </td>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                <strong>Non-Scheduled Day Example:</strong>
                <br>
                A WAL carrier works:
                <br>
                • Total hours worked: 8 hours
                <br>
                • All hours are off-assignment
                <br><br>
                Remedy = 8.00 (NS day)
            </p>
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the OTDL was maximized that day</li>
    <li>When the carrier is on the OTDL or is a PTF</li>
    <li>When no overtime was worked</li>
    <li>When overtime was worked only on their own assignment</li>
</ul>
"""

DOCUMENTATION_85F = """
<h2 style='color: #BB86FC;'>Article 8.5.F - Over 10 Hours Off Assignment</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"Excluding December, no full-time regular employee will be required to work... over ten (10) hours on a regularly 
scheduled day..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The carrier worked more than 10 hours total in a day</li>
    <li>Some portion of those hours were worked off their assignment</li>
    <li>It is not during the month of December</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>First, calculate hours worked beyond 10:
        <br>• Take the total hours worked that day
        <br>• Subtract 10 hours
        <br>• This gives you the hours over 10
    </li>
    <li>Next, determine how many hours were worked off assignment:
        <br>• Add up all the time spent working routes other than their own
        <br>• This gives you the off-assignment hours
    </li>
    <li>The remedy will be the smaller of these two numbers:
        <br>• If they worked more hours off assignment than hours over 10, the remedy is the hours over 10
        <br>• If they worked more hours over 10 than off assignment hours, the remedy is the off-assignment hours
    </li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    A WAL carrier has the following hours:
    <br><br>
    • Total hours worked: 11.50 hours
    <br>
    • Hours on other routes: 2.00 hours
    <br><br>
    Remedy Calculation:
    <br>
    • Hours over 10 = 11.50 - 10 = 1.50 hours
    <br>
    • Hours off assignment = 2.00 hours
    <br>
    • Remedy = 1.50 hours (the lesser of 1.50 hours over 10 or 2.00 off-assignment hours)
</p>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the carrier is on the OTDL</li>
    <li>When total hours worked is 10 or less</li>
    <li>When all overtime work is on their own assignment</li>
    <li>During the month of December (penalty overtime exclusion period)</li>
</ul>
"""

DOCUMENTATION_85F_NS = """
<h2 style='color: #BB86FC;'>Article 8.5.F - Non-Scheduled Day Overtime</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"Excluding December, no full-time regular employee will be required to work... "
"over eight (8) hours on a non-scheduled day..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The carrier worked more than 8 hours on their non-scheduled day</li>
    <li>It is not during the month of December</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>First, identify if it's a non-scheduled day:
        <br>• Check if the day is coded as "NS Day"
    </li>
    <li>Then, calculate hours worked beyond 8:
        <br>• Take the total hours worked that day
        <br>• Subtract 8 hours
        <br>• This gives you the remedy hours
    </li>
</ol>

<p><strong>Note:</strong> Unlike regular overtime violations, ALL hours worked beyond 8 on a \
non-scheduled day count toward the remedy, regardless of whether they were worked on or \
off assignment.</p>

<h3 style='color: #03DAC6;'>Example:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    A WAL carrier on their non-scheduled day:
    <br><br>
    • Total hours worked: 10 hours
    <br><br>
    Remedy Calculation:
    <br>
    • Hours over 8 = 10 - 8 = 2 hours
    <br>
    • Remedy = 2 hours
</p>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the carrier is on the OTDL</li>
    <li>When total hours worked is 8 or less on the NS day</li>
    <li>When it's a regularly scheduled day</li>
    <li>During the month of December (penalty overtime exclusion period)</li>
</ul>
"""

DOCUMENTATION_85F_5TH = """
<h2 style='color: #BB86FC;'>Article 8.5.F - More Than 4 Days of Overtime in a Week</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    "Excluding December, no full-time regular employee will be required to work overtime "
    "on more than four (4) of the employee's five (5) scheduled days in a service week..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The carrier has already worked overtime on 4 days this service week</li>
    <li>The carrier is required to work overtime on a 5th day</li>
    <li>The carrier did not have any days where they worked between 0.01 and 8.00 hours \
(excluding Sundays)</li>
    <li>It is not during the month of December</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>Track overtime days in the service week:
        <br>• Count each day where total hours exceed 8
        <br>• Include both work hours and paid leave hours
    </li>
    <li>Check for 8-hour days:
        <br>• Look for any day (except Sunday) where hours worked are between 0.01 and 8.00
        <br>• Days not worked (0.00 hours) do not count as 8-hour days
        <br>• If a qualifying 8-hour day is found, no violation occurs
    </li>
    <li>On the 5th overtime day (if no 8-hour days found):
        <br>• Take the total hours worked that day
        <br>• Subtract 8 hours
        <br>• This amount becomes the remedy
    </li>
</ol>

<p><strong>Note:</strong> All overtime hours worked on the 5th day count toward the remedy, \
regardless of whether they were worked on or off assignment.</p>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; margin-bottom: 20px;'><tr>
    <td style='width: 60%; vertical-align: top; padding-right: 20px;'>
        <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
            Example 1 - Violation:
            <br>
            A WAL carrier's service week with no 8-hour days:
            <br>
            • Saturday: 0.00 (not worked - does not prevent violation)
            <br>
            • Monday: 9.5 hours (1st overtime day)
            <br>
            • Tuesday: 10.5 hours (2nd overtime day)
            <br>
            • Wednesday: 10 hours (3rd overtime day)
            <br>
            • Thursday: 9.25 hours (4th overtime day)
            <br>
            • Friday: 9.75 hours (5th overtime day - VIOLATION)
            <br><br>
            Remedy Calculation:
            <br>
            • Hours over 8 on Friday = 9.75 - 8 = 1.75 hours
            <br>
            • Remedy = 1.75 hours
        </p>
    </td>
    
    <td style='width: 40%; vertical-align: top;'>
        <table style='width: 100%; border-collapse: collapse; \
background-color: #2D2D2D;'>
            <tr style='background-color: #1E1E1E;'>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Date</th>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Hours</th>
            </tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Sat</td>
                <td style='padding: 8px; border: 1px solid #444;'>0.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Mon</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.50</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Tue</td>
                <td style='padding: 8px; border: 1px solid #444;'>10.50</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Wed</td>
                <td style='padding: 8px; border: 1px solid #444;'>10.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Thu</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.25</td></tr>
            <tr style='background-color: #BB86FC; color: #000000;'>
                <td style='padding: 8px; border: 1px solid #444;'>Fri</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.75</td></tr>
        </table>
    </td>
</tr></table>

<table style='width: 100%; border: none;'><tr>
    <td style='width: 60%; vertical-align: top; padding-right: 20px;'>
        <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
            Example 2 - No Violation:
            <br>
            A WAL carrier's service week with an 8-hour day:
            <br>
            • Saturday: 9 hours (1st overtime day)
            <br>
            • Monday: 9.5 hours (2nd overtime day)
            <br>
            • Tuesday: 7.5 hours (prevents violation)
            <br>
            • Wednesday: 10 hours (3rd overtime day)
            <br>
            • Thursday: 9.25 hours (4th overtime day)
            <br>
            • Friday: 9 hours (5th overtime day - NO VIOLATION)
        </p>
    </td>
    
    <td style='width: 40%; vertical-align: top;'>
        <table style='width: 100%; border-collapse: collapse; \
background-color: #2D2D2D;'>
            <tr style='background-color: #1E1E1E;'>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Date</th>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Hours</th>
            </tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Sat</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Mon</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.50</td></tr>
            <tr style='background-color: #03DAC622;'>
                <td style='padding: 8px; border: 1px solid #444;'>Tue</td>
                <td style='padding: 8px; border: 1px solid #444;'>7.50</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Wed</td>
                <td style='padding: 8px; border: 1px solid #444;'>10.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Thu</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.25</td></tr>
            <tr style='background-color: #383838;'>
                <td style='padding: 8px; border: 1px solid #444;'>Fri</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.00</td></tr>
        </table>
    </td>
</tr></table>

<table style='width: 100%; border: none;'><tr>
    <td style='width: 60%; vertical-align: top; padding-right: 20px;'>
        <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
            Example 3 - Small Remedy:
            <br><br>
            • WAL carrier works 10 hours (2 hours overtime)
            <br>
            • OTDL carrier worked 11.50 hours
            <br>
            • OTDL carrier's limit is 12 hours
            <br>
            • OTDL carrier was not excused
            <br><br>
            Remedy Calculation:
            <br>
            • Available hours = 12 - 11.50 = 0.50 hours
            <br>
            • Remedy = 0.50 hours (Any available time generates a remedy)
        </p>
    </td>
    
    <td style='width: 40%; vertical-align: top;'>
        <table style='width: 100%; border-collapse: collapse; \
background-color: #2D2D2D;'>
            <tr style='background-color: #1E1E1E;'>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Date</th>
                <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Hours</th>
            </tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Sat</td>
                <td style='padding: 8px; border: 1px solid #444;'>0.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Mon</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.50</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Tue</td>
                <td style='padding: 8px; border: 1px solid #444;'>10.50</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Wed</td>
                <td style='padding: 8px; border: 1px solid #444;'>10.00</td></tr>
            <tr><td style='padding: 8px; border: 1px solid #444;'>Thu</td>
                <td style='padding: 8px; border: 1px solid #444;'>9.25</td></tr>
            <tr style='background-color: #BB86FC; color: #000000;'>
                <td style='padding: 8px; border: 1px solid #444;'>Fri</td>
                <td style='padding: 8px; border: 1px solid #444;'>11.50</td></tr>
        </table>
    </td>
</tr></table>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the carrier is on the OTDL</li>
    <li>When overtime is worked on 4 or fewer days in the service week</li>
    <li>When the carrier has worked between 0.01 and 8.00 hours on any day \
(excluding Sundays)</li>
    <li>During the month of December (penalty overtime exclusion period)</li>
    <li>When the 5th day's total hours are 8 or less</li>
</ul>

<p><strong>Note:</strong> Days not worked (0.00 hours) do not count as 8-hour days and \
will not prevent a violation.</p>
"""

DOCUMENTATION_MAX12 = """
<h2 style='color: #BB86FC;'>Maximum Daily Work Hour Limitations - 12 Hours</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    "Full-time employees are prohibited from working more than 12 hours in a single \
work day..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when:</p>
<ul>
    <li>A full-time carrier works more than 12 hours in a day</li>
    <li>For WAL carriers, the limit is 11.50 hours</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>Take the total hours worked that day</li>
    <li>Subtract the applicable limit (12.00 or 11.50)</li>
    <li>This amount becomes the remedy</li>
</ol>
"""

DOCUMENTATION_MAX60 = """
<h2 style='color: #BB86FC;'>Maximum Weekly Work Hour Limit - 60 Hours</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    "Full-time employees are prohibited from working more than... 60 hours within a \
service week."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when:</p>
<ul>
    <li>A carrier's total work hours in a service week exceed 60 hours</li>
    <li>The carrier is WAL, NL, or OTDL (PTFs are exempt)</li>
    <li>It is not during December</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>Calculate total weekly hours:
        <br>• Add all work hours for the service week
        <br>• Include paid leave hours
        <br>• Include holiday pay hours
    </li>
    <li>If total exceeds 60 hours:
        <br>• Subtract 60 from the total weekly hours
        <br>• This amount becomes the remedy
    </li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; \
border-spacing: 20px 0;'>
    <tr>
        <td style='width: 60%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                A WAL carrier's service week:
                <br>
                • Saturday: 10 hours
                <br>
                • Monday: 12 hours
                <br>
                • Tuesday: 11 hours
                <br>
                • Wednesday: 11 hours
                <br>
                • Thursday: 10 hours
                <br>
                • Friday: 8 hours
                <br><br>
                Weekly Total: 62 hours
                <br>
                Remedy = 62 - 60 = 2 hours
            </p>
        </td>
        
        <td style='width: 40%; vertical-align: top;'>
            <table style='width: 100%; border-collapse: collapse; \
background-color: #2D2D2D;'>
                <tr style='background-color: #1E1E1E;'>
                    <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Date</th>
                    <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Hours</th>
                    <th style='padding: 8px; border: 1px solid #444; \
color: #BB86FC;'>Total</th>
                </tr>
                <tr><td style='padding: 8px; border: 1px solid #444;'>Sat</td>
                    <td style='padding: 8px; border: 1px solid #444;'>10.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>10.00</td></tr>
                <tr><td style='padding: 8px; border: 1px solid #444;'>Mon</td>
                    <td style='padding: 8px; border: 1px solid #444;'>12.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>22.00</td></tr>
                <tr><td style='padding: 8px; border: 1px solid #444;'>Tue</td>
                    <td style='padding: 8px; border: 1px solid #444;'>11.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>33.00</td></tr>
                <tr><td style='padding: 8px; border: 1px solid #444;'>Wed</td>
                    <td style='padding: 8px; border: 1px solid #444;'>11.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>44.00</td></tr>
                <tr><td style='padding: 8px; border: 1px solid #444;'>Thu</td>
                    <td style='padding: 8px; border: 1px solid #444;'>10.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>54.00</td></tr>
                <tr style='background-color: #BB86FC; color: #000000;'>
                    <td style='padding: 8px; border: 1px solid #444;'>Fri</td>
                    <td style='padding: 8px; border: 1px solid #444;'>8.00</td>
                    <td style='padding: 8px; border: 1px solid #444;'>62.00</td></tr>
            </table>
            <p style='color: #BB86FC; margin-top: 10px;'>Remedy = 2.00 hours</p>
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When total weekly hours are 60 or less</li>
    <li>When the carrier is a PTF</li>
    <li>During the month of December (in Billings)</li>
</ul>

<p><strong>Important Notes:</strong></p>
<ul>
    <li>Once a carrier reaches 20 hours of overtime in a week, they are no longer \
available for additional overtime (except in December)</li>
    <li>A carrier's tour of duty should be terminated when they reach 60 hours</li>
    <li>All types of paid leave count toward the 60-hour limit</li>
</ul>
"""

DOCUMENTATION_85G = """
<h2 style='color: #BB86FC;'>Article 8.5.G - OTDL Not Maximized</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    "Full-time employees not on the 'Overtime Desired' list may be required to work overtime only if all available employees on the 
    'Overtime Desired' list have worked up to twelve (12) hours in a day or sixty (60) hours in a service week."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>A WAL or NL carrier works overtime off their assignment</li>
    <li>An OTDL carrier was available to work (not excused)</li>
    <li>The available OTDL carrier had not reached their daily limit (12 hours, or more in December)</li>
    <li>The available OTDL carrier had not reached their weekly limit (60 hours, or more in December)</li>
</ul>

<h3 style='color: #03DAC6;'>Special Notes About December:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    During December (penalty overtime exclusion period):
    <br>• OTDL carriers may work beyond 12 hours per day and 60 hours per week
    <br>• Management may, but is not required to, assign OTDL carriers beyond these limits
    <br>• The requirement to maximize OTDL carriers before using WAL/NL carriers still applies
    <br>• Violations still occur if WAL/NL carriers work overtime when OTDL carriers are available
</p>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>For each OTDL carrier:
        <br>• Determine their hour limit (usually 12.00)
        <br>• Calculate how many more hours they could have worked
        <br>• Remedy = hour_limit - total_hours
    </li>
    <li>Special Cases:
        <br>• If carrier is excused (sick, annual, holiday, etc.), no violation occurs
        <br>• If carrier has reached their hour limit, no violation occurs
        <br>• If OTDL is marked as maximized for the day, no violation occurs
    </li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 1 - Violation:
                <br><br>
                • WAL carrier works 10 hours (2 hours overtime)
                <br>
                • OTDL carrier only worked 8 hours
                <br>
                • OTDL carrier's limit is 12 hours
                <br>
                • OTDL carrier was not excused
                <br><br>
                Remedy Calculation:
                <br>
                • Available hours = 12 - 8 = 4 hours
                <br>
                • Remedy = 4.00 hours
            </p>
        </td>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 2 - No Violation:
                <br><br>
                • WAL carrier works 10 hours (2 hours overtime)
                <br>
                • OTDL carrier worked 12.00 hours
                <br>
                • OTDL carrier's limit is 12 hours
                <br>
                • OTDL carrier is maximized
                <br><br>
                Result:
                <br>
                • No violation - OTDL carrier at maximum limit
            </p>
        </td>
    </tr>
    <tr>
        <td colspan="2" style='padding-top: 20px;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 3 - Small Remedy:
                <br><br>
                • WAL carrier works 10 hours (2 hours overtime)
                <br>
                • OTDL carrier worked 11.50 hours
                <br>
                • OTDL carrier's limit is 12 hours
                <br>
                • OTDL carrier was not excused
                <br><br>
                Remedy Calculation:
                <br>
                • Available hours = 12 - 11.50 = 0.50 hours
                <br>
                • Remedy = 0.50 hours (Any available time generates a remedy)
            </p>
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When OTDL carriers are marked as maximized for the day</li>
    <li>When OTDL carriers are excused (sick, annual, holiday, etc.)</li>
    <li>When OTDL carriers have reached their hour limits (12/60, or higher in December)</li>
    <li>When no WAL/NL carriers work overtime off assignment</li>
    <li>On Sundays</li>
</ul>

<h3 style='color: #03DAC6;'>Special Notes:</h3>
<ul>
    <li>Excusal reasons are tracked in the OTDL Maximization pane</li>
    <li>Each OTDL carrier's hour limit can be customized in The Carrier List</li>
    <li>The OTDL Maximization pane allows marking entire days as maximized</li>
    <li>Individual carriers can be excused for specific dates</li>
</ul>
"""

# Continue with other documentation strings
