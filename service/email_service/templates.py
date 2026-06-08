LOGO_URL = "https://diplicity.com/otto.png"


def notification_email(title, body, link=None, link_text="View Game"):
    cta_block = ""
    if link:
        cta_block = f"""
          <tr>
            <td class="pad-md" align="center" style="padding: 28px 44px 8px;">
              <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link}" style="height:48px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#1c1a14">
                  <w:anchorlock/>
                  <center style="color:#f5efe0;font-family:Georgia,serif;font-size:15px;letter-spacing:0.18em;text-transform:uppercase;">{link_text} &#8594;</center>
                </v:roundrect>
              <![endif]-->
              <!--[if !mso]><!-- -->
              <a class="btn-a" href="{link}" style="display:inline-block; background:#1c1a14; color:#f5efe0; text-decoration:none; padding: 16px 36px; font-family: Georgia, serif; font-size: 14px; letter-spacing: 0.20em; text-transform: uppercase; border:1px solid #1c1a14;">
                {link_text} &nbsp;&rarr;
              </a>
              <!--<![endif]-->
            </td>
          </tr>"""

    return f"""<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <title>{title}</title>
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    @media only screen and (max-width: 480px) {{
      .container {{ width: 100% !important; padding: 24px 20px !important; }}
      .h1        {{ font-size: 28px !important; line-height: 1.15 !important; }}
      .btn-a     {{ display: block !important; width: 100% !important; box-sizing: border-box; }}
      .stamp     {{ font-size: 10px !important; }}
      .pad-md    {{ padding: 28px 22px !important; }}
    }}
  </style>
</head>
<body style="margin:0; padding:0; background:#ece4d3; font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif; color:#23201a;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all; font-size:1px; line-height:1px; color:#ece4d3;">
    {body} &#8199;&#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp;
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ece4d3;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px; background:#f5efe0; border:1px solid #d8cdb4;">
          <tr>
            <td style="padding: 0; border-bottom: 1px dashed #b3a685;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="left"  style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">Diplomatic Cable</td>
                  <td align="right" style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">Notification</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 44px 44px 8px;">
              <img src="{LOGO_URL}" width="56" height="56" alt="Diplicity" style="display:block; width:56px; height:56px; border:0; outline:none; border-radius:50%;">
              <h1 class="h1" style="margin: 22px 0 0; font-family: Georgia, 'Iowan Old Style', serif; font-weight: 400; font-size: 34px; line-height: 1.1; letter-spacing:-0.01em; color:#1c1a14;">
                {title}
              </h1>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 22px 44px 8px; font-family: Georgia, serif; font-size: 16px; line-height: 1.65; color:#3a3527;">
              <p style="margin: 0;">{body}</p>
            </td>
          </tr>
          {cta_block}
          <tr>
            <td class="pad-md" style="padding: 28px 44px 0;">
              <div style="border-top:1px dashed #b3a685; line-height:0; height:0;">&nbsp;</div>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 6px; font-family: Georgia, serif; font-size: 13px; line-height: 1.6; color:#5b4a36;">
              <p style="margin:0;"><em>You received this because you have email notifications enabled. You can disable them in your profile settings.</em></p>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 36px; font-family: Georgia, serif; font-size: 14px; line-height: 1.6; color:#3a3527;">
              <p style="margin:0;">&mdash; The Diplicity volunteers</p>
            </td>
          </tr>
        </table>
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px;">
          <tr>
            <td align="center" style="padding: 22px 24px 8px; font-family: Georgia, serif; font-size: 12px; line-height: 1.6; color:#7a6843;">
              <a href="https://discord.gg/GyqEmaWS" style="color:#5b4a36; text-decoration:underline;">Discord</a>
              &nbsp;&middot;&nbsp;
              <a href="https://diplicity.com" style="color:#5b4a36; text-decoration:underline;">diplicity.com</a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 4px 24px 28px; font-family: Georgia, serif; font-size: 11px; line-height: 1.6; color:#9b8a64; letter-spacing: 0.12em; text-transform: uppercase;">
              Diplicity &middot; Since 2014
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
