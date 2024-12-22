"""Documentation content for Article 8 violations formulas."""

DOCUMENTATION_85D = """
<h2 style='color: #BB86FC;'>Article 8.5.D - Overtime Off Assignment</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    "<strong style='color: #BB86FC;'>If the voluntary 'Overtime Desired' list does not provide sufficient qualified people</strong>, "
    "qualified full-time regular employees not on the list may be required to work overtime "
    "on a rotating basis with the first opportunity assigned to the junior employee."
</p>
<p style='font-style: italic; color: #03DAC6; margin-top: 10px;'>
    Note: This language establishes a crucial requirement - management must first attempt to use all available OTDL carriers 
    to their maximum daily (12 hours) and weekly (60 hours) limits before requiring WAL or NL carriers to work overtime off 
    their assignment. This is why checking if the OTDL was maximized is a key condition for violations.
</p>
<p style='font-style: italic; color: #03DAC6; margin-top: 10px;'>
    Display Indicator: When a violation occurs on a carrier's non-scheduled day, you will see "(NS day)" next to the remedy amount. 
    This indicates that the carrier is entitled to the full day's hours as remedy, rather than just the overtime portion.
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
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
"<strong style='color: #BB86FC;'>Excluding December</strong>, no full-time regular employee will be required to work... <strong style='color: #BB86FC;'>over ten (10) hours on a regularly scheduled day</strong>..."
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
"<strong style='color: #BB86FC;'>Excluding December</strong>, no full-time regular employee will be required to work... <strong style='color: #BB86FC;'>over eight (8) hours on a non-scheduled day</strong>..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The day is coded as "NS Day" in the carrier's schedule</li>
    <li>The carrier worked more than 8 hours on this non-scheduled day</li>
    <li>It is not during the month of December</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<ol>
    <li>First, verify the day is coded as "NS Day"</li>
    <li>Calculate hours worked beyond 8:
        <br>• Take the total hours worked that day
        <br>• Subtract 8 hours
        <br>• Round to 2 decimal places
        <br>• This gives you the remedy hours
    </li>
</ol>

<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
<strong>Important:</strong> Unlike regular overtime violations, ALL hours worked beyond 8 on a non-scheduled day count toward the remedy, regardless of whether they were worked on or off assignment.
</p>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 1 - Violation:
                <br><br>
                • WAL carrier on NS day
                <br>
                • Total hours worked: 10.00
                <br><br>
                Remedy Calculation:
                <br>
                • Hours over 8 = 10.00 - 8.00
                <br>
                • Remedy = 2.00 hours
            </p>
        </td>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 2 - No Violation:
                <br><br>
                • WAL carrier on NS day
                <br>
                • Total hours worked: 8.00
                <br><br>
                Result:
                <br>
                • No violation - At or under 8 hours
            </p>
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>Violation Types:</h3>
<ul>
    <li><strong>8.5.F NS Overtime On a Non-Scheduled Day</strong> - More than 8 hours worked on NS day</li>
    <li><strong>No Violation (December Exclusion)</strong> - During December exclusion period</li>
    <li><strong>No Violation</strong> - All other cases</li>
</ul>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the carrier is on the OTDL</li>
    <li>When total hours worked is 8 or less on the NS day</li>
    <li>When it's a regularly scheduled day</li>
    <li>During the month of December (penalty overtime exclusion period)</li>
</ul>

<h3 style='color: #03DAC6;'>Special Notes:</h3>
<ul>
    <li>The day must be explicitly coded as "NS Day" to trigger violation checks</li>
    <li>All hours beyond 8 count toward the remedy, regardless of assignment</li>
    <li>Remedies are always rounded to 2 decimal places</li>
    <li>December exclusion applies to all carriers</li>
</ul>
"""

DOCUMENTATION_85F_5TH = """
<h2 style='color: #BB86FC;'>Article 8.5.F - More Than 4 Days of Overtime in a Week</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"<strong style='color: #BB86FC;'>Excluding December</strong>, no full-time regular employee will be required to work overtime on <strong style='color: #BB86FC;'>more than four (4) of the employee's five (5) scheduled days in a service week</strong>..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>The carrier is Work Assignment List (WAL) or No List</li>
    <li>The carrier has already worked overtime on 4 days this service week</li>
    <li>The carrier is required to work overtime on a 5th day</li>
    <li>The carrier did not have any days where they worked between 0.01 and 8.00 hours (excluding Sundays)</li>
    <li>It is not during the month of December</li>
</ul>

<h3 style='color: #03DAC6;'>How Daily Hours Are Calculated:</h3>
<p>The system calculates daily hours as follows:</p>
<ul>
    <li>For regular work days:
        <br>• If leave hours ≤ work hours: Use the larger of the two
        <br>• If leave hours > work hours: Add them together
    </li>
    <li>For holidays:
        <br>• If holiday leave is exactly 8.00 hours: Use only work hours
        <br>• Otherwise, follow regular work day rules
    </li>
</ul>

<h3 style='color: #03DAC6;'>Service Week Rules:</h3>
<ul>
    <li>Service week runs from Saturday to Friday</li>
    <li>Sundays are excluded from overtime day counts</li>
    <li>Days not worked (0.00 hours) do not count as 8-hour days</li>
    <li>Only days with more than 8 hours count as overtime days</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<ol>
    <li>Track overtime days in the service week:
        <br>• Count each day where total hours exceed 8
        <br>• Include both work hours and paid leave hours
        <br>• Exclude Sundays
    </li>
    <li>Check for 8-hour days:
        <br>• Look for any day (except Sunday) where hours worked are between 0.01 and 8.00
        <br>• Days not worked (0.00 hours) do not count as 8-hour days
        <br>• If a qualifying 8-hour day is found, no violation occurs
    </li>
    <li>On the 5th overtime day (if no 8-hour days found):
        <br>• Take the total hours worked that day
        <br>• Subtract 8 hours
        <br>• Round to 2 decimal places
        <br>• This amount becomes the remedy
    </li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 60%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 1 - Violation:
                <br>
                A WAL carrier's service week with no 8-hour days:
                <br>
                • Saturday: 0.00 (not worked - does not prevent violation)
                <br>
                • Monday: 9.50 hours (1st overtime day)
                <br>
                • Tuesday: 10.50 hours (2nd overtime day)
                <br>
                • Wednesday: 10.00 hours (3rd overtime day)
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
            <table style='width: 100%; border-collapse: collapse; background-color: #2D2D2D;'>
                <tr style='background-color: #1E1E1E;'>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Date</th>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Hours</th>
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
    </tr>
</table>

<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 60%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 2 - No Violation:
                <br>
                A WAL carrier's service week with an 8-hour day:
                <br>
                • Saturday: 9.00 hours (1st overtime day)
                <br>
                • Monday: 9.50 hours (2nd overtime day)
                <br>
                • Tuesday: 7.50 hours (prevents violation)
                <br>
                • Wednesday: 10.00 hours (3rd overtime day)
                <br>
                • Thursday: 9.25 hours (4th overtime day)
                <br>
                • Friday: 9.00 hours (5th overtime day - NO VIOLATION)
            </p>
        </td>
        <td style='width: 40%; vertical-align: top;'>
            <table style='width: 100%; border-collapse: collapse; background-color: #2D2D2D;'>
                <tr style='background-color: #1E1E1E;'>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Date</th>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Hours</th>
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
    </tr>
</table>

<h3 style='color: #03DAC6;'>Violation Types:</h3>
<ul>
    <li><strong>8.5.F 5th More Than 4 Days of Overtime in a Week</strong> - Fifth overtime day with no 8-hour days</li>
    <li><strong>No Violation (December Exclusion)</strong> - During December exclusion period</li>
    <li><strong>No Violation</strong> - All other cases</li>
</ul>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When the carrier is on the OTDL</li>
    <li>When overtime is worked on 4 or fewer days in the service week</li>
    <li>When the carrier has worked between 0.01 and 8.00 hours on any day (excluding Sundays)</li>
    <li>During the month of December (penalty overtime exclusion period)</li>
    <li>When the 5th day's total hours are 8 or less</li>
</ul>

<h3 style='color: #03DAC6;'>Special Notes:</h3>
<ul>
    <li>Service weeks are always Saturday to Friday</li>
    <li>Days not worked (0.00 hours) do not count as 8-hour days</li>
    <li>Sundays are excluded from all calculations</li>
    <li>Holiday hours are handled specially (see Daily Hours section)</li>
    <li>All remedies are rounded to 2 decimal places</li>
</ul>
"""

DOCUMENTATION_MAX12 = """
<h2 style='color: #BB86FC;'>Maximum 12 Hours in a Day</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"Employees shall <strong style='color: #BB86FC;'>not be required to work more than 12 hours in one service day</strong>..."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when a carrier exceeds their maximum daily limit:</p>
<ul>
    <li>WAL carriers:
        <br>• 11.50 hours if moved between routes
        <br>• 12.00 hours if working only their assignment
    </li>
    <li>NL/PTF carriers: 11.50 hours maximum</li>
    <li>OTDL carriers: 12.00 hours maximum</li>
</ul>

<h3 style='color: #03DAC6;'>December Rules:</h3>
<ul>
    <li>OTDL carriers are exempt from MAX12 violations</li>
    <li>WAL carriers working only their assignment are exempt</li>
    <li>WAL carriers working off assignment CAN trigger MAX12 (treated as NL)</li>
    <li>NL/PTF carriers can still trigger MAX12 violations</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>The remedy is all hours worked beyond the applicable limit:</p>
<ul>
    <li>Hours beyond 11.50 for NL, PTF, and WAL carriers working multiple routes</li>
    <li>Hours beyond 12.00 for OTDL and WAL carriers on their assignment only</li>
</ul>

<h3 style='color: #03DAC6;'>Example:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    A WAL carrier working multiple routes:
    <br>• Total hours worked: 12.00 hours
    <br>• Maximum allowed: 11.50 hours
    <br>• Remedy = 0.50 hours
</p>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>OTDL carriers in December</li>
    <li>WAL carriers working only their assignment in December</li>
    <li>When total hours are under the applicable limit</li>
</ul>
"""

DOCUMENTATION_MAX60 = """
<h2 style='color: #BB86FC;'>Maximum 60 Hours in a Service Week</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"<strong style='color: #BB86FC;'>Full-time employees shall not be permitted to work more than 60 hours within a service week</strong>."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>A carrier's total weekly hours exceed 60 hours</li>
    <li>The carrier is WAL, NL, or OTDL (PTFs are exempt)</li>
    <li>It is not during December (in Billings, MT)</li>
</ul>

<h3 style='color: #03DAC6;'>How Weekly Hours Are Calculated:</h3>
<p>The following are included in the 60-hour total:</p>
<ul>
    <li>Regular work hours</li>
    <li>Paid leave hours (sick leave, annual leave, etc.)</li>
    <li>Holiday pay hours</li>
</ul>

<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
    <strong>Important:</strong> When a carrier has both work hours and leave hours on the same day:
    <br>• If leave hours ≤ work hours: The larger of the two is used
    <br>• If leave hours > work hours: Both are added together
</p>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>To calculate the remedy amount:</p>
<ol>
    <li>Add up all hours for the service week (work + leave)</li>
    <li>If total exceeds 60 hours:
        <br>• Subtract 60 from the total weekly hours
        <br>• Round to 2 decimal places
        <br>• This amount becomes the remedy
    </li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 60%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                A WAL carrier's service week:
                <br>• Saturday: 10 hours
                <br>• Monday: 12 hours
                <br>• Tuesday: 11 hours
                <br>• Wednesday: 11 hours
                <br>• Thursday: 10 hours
                <br>• Friday: 8 hours
                <br><br>
                Weekly Total: 62 hours
                <br>
                Remedy = 62 - 60 = 2.00 hours
            </p>
        </td>
        <td style='width: 40%; vertical-align: top;'>
            <table style='width: 100%; border-collapse: collapse; background-color: #2D2D2D;'>
                <tr style='background-color: #1E1E1E;'>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Date</th>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Hours</th>
                    <th style='padding: 8px; border: 1px solid #444; color: #BB86FC;'>Total</th>
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
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When total weekly hours are 60 or less</li>
    <li>When the carrier is a PTF</li>
    <li>During the month of December (in Billings)</li>
</ul>

<h3 style='color: #03DAC6;'>Important Notes:</h3>
<ul>
    <li>Once a carrier reaches 20 hours of overtime in a week, they should not be assigned additional overtime</li>
    <li>A carrier's tour of duty should be terminated when they reach 60 hours</li>
    <li>The violation is only reported on the last day of the service week when the total exceeds 60 hours</li>
    <li>All carriers are exempt from the 60-hour limit during December in Billings, MT</li>
</ul>
"""

DOCUMENTATION_85G = """
<h2 style='color: #BB86FC;'>Article 8.5.G - OTDL Not Maximized</h2>

<h3 style='color: #03DAC6;'>Contract Language:</h3>
<p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
"<strong style='color: #BB86FC;'>Full-time employees not on the 'Overtime Desired' list may be required to work overtime only if all available employees on the 'Overtime Desired' list have worked up to twelve (12) hours in a day or sixty (60) hours in a service week</strong>."
</p>

<h3 style='color: #03DAC6;'>When Does a Violation Occur?</h3>
<p>A violation occurs when ALL of these conditions are met:</p>
<ul>
    <li>A WAL or NL carrier works overtime (more than 8 hours)</li>
    <li>An OTDL carrier was available to work (not excused)</li>
    <li>The available OTDL carrier had not reached their daily limit (usually 12 hours)</li>
    <li>The day was not marked as "OTDL Maximized" in the OTDL Maximization pane</li>
</ul>

<h3 style='color: #03DAC6;'>Automatic Excusal Conditions:</h3>
<p>OTDL carriers are automatically excused when any of these exact indicators appear:</p>
<ul>
    <li>(sick) - On sick leave</li>
    <li>(NS protect) - Non-scheduled day protection</li>
    <li>(holiday) - Holiday leave</li>
    <li>(guaranteed) - Guaranteed time</li>
    <li>(annual) - Annual leave</li>
    <li>Sundays - All carriers are excused on Sundays</li>
</ul>

<h3 style='color: #03DAC6;'>Manual Excusal Options:</h3>
<ul>
    <li>Mark entire days as "OTDL Maximized" in the OTDL Maximization pane</li>
    <li>Excuse individual carriers for specific dates</li>
    <li>Set custom hour limits for individual carriers in The Carrier List</li>
</ul>

<h3 style='color: #03DAC6;'>How is the Remedy Calculated?</h3>
<p>For each OTDL carrier that was not maximized or excused:</p>
<ol>
    <li>Take their hour limit (usually 12.00 hours)</li>
    <li>Subtract their total hours worked that day</li>
    <li>Round to 2 decimal places</li>
    <li>This amount becomes their remedy</li>
</ol>

<h3 style='color: #03DAC6;'>Example:</h3>
<table style='width: 100%; border: none; border-collapse: separate; border-spacing: 20px 0;'>
    <tr>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 1 - Violation:
                <br><br>
                • WAL carrier works 10.00 hours (2 hours overtime)
                <br>
                • OTDL carrier only worked 8.00 hours
                <br>
                • OTDL carrier's limit is 12.00 hours
                <br>
                • OTDL carrier was not excused
                <br><br>
                Remedy Calculation:
                <br>
                • Available hours = 12.00 - 8.00 = 4.00 hours
                <br>
                • Remedy = 4.00 hours
            </p>
        </td>
        <td style='width: 50%; vertical-align: top;'>
            <p style='background-color: #2D2D2D; padding: 10px; border-radius: 4px;'>
                Example 2 - No Violation:
                <br><br>
                • WAL carrier works 10.00 hours (2 hours overtime)
                <br>
                • OTDL carrier worked 12.00 hours
                <br>
                • OTDL carrier's limit is 12.00 hours
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
                • WAL carrier works 10.00 hours (2 hours overtime)
                <br>
                • OTDL carrier worked 11.50 hours
                <br>
                • OTDL carrier's limit is 12.00 hours
                <br>
                • OTDL carrier was not excused
                <br><br>
                Remedy Calculation:
                <br>
                • Available hours = 12.00 - 11.50 = 0.50 hours
                <br>
                • Remedy = 0.50 hours (Any available time generates a remedy)
            </p>
        </td>
    </tr>
</table>

<h3 style='color: #03DAC6;'>Violation Types:</h3>
<ul>
    <li><strong>8.5.G OTDL Not Maximized</strong> - OTDL carrier had available hours</li>
    <li><strong>8.5.G Trigger (No Remedy)</strong> - WAL/NL carrier that triggered the violation</li>
    <li><strong>No Violation (Auto Excused)</strong> - Carrier has an auto-excusal indicator</li>
    <li><strong>No Violation (Manually Excused)</strong> - Carrier was manually excused</li>
    <li><strong>No Violation (Maximized)</strong> - Carrier reached their hour limit</li>
    <li><strong>No Violation (Non OTDL)</strong> - Not an OTDL carrier</li>
</ul>

<h3 style='color: #03DAC6;'>No Violation Cases:</h3>
<ul>
    <li>When OTDL carriers are marked as maximized for the day</li>
    <li>When OTDL carriers are excused (sick, annual, holiday, etc.)</li>
    <li>When OTDL carriers have reached their hour limits</li>
    <li>When no WAL/NL carriers work overtime</li>
    <li>On Sundays</li>
</ul>

<h3 style='color: #03DAC6;'>Special Notes:</h3>
<ul>
    <li>The trigger carrier (WAL/NL working overtime) with the most hours is recorded</li>
    <li>Each OTDL carrier's hour limit can be customized in The Carrier List</li>
    <li>The OTDL Maximization pane allows marking entire days as maximized</li>
    <li>Individual carriers can be excused for specific dates</li>
    <li>All remedies are rounded to 2 decimal places</li>
    <li>Excusal indicators must match exactly (e.g., "(sick)" not "sick")</li>
    <li>Hour limits default to 12.00 if not specified</li>
</ul>
"""

# Continue with other documentation strings
