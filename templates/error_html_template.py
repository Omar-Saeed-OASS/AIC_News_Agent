from datetime import datetime, date

error_html_content = """
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; background-color: #fef2f2; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e1b4b; line-height: 1.6;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #fef2f2; padding: 32px 16px;">
                <tr>
                  <td align="center">
                    <!-- Main Container Card -->
                    <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(153, 27, 27, 0.1); border: 1px solid #fecaca;">

                      <!-- Alert Header Gradient Banner -->
                      <tr>
                        <td style="background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 55%, #b91c1c 100%); padding: 30px; text-align: left;">
                          <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.15); border: 1px solid rgba(254, 202, 202, 0.4); border-radius: 20px; padding: 4px 12px; margin-bottom: 12px;">
                            <span style="font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #fecaca;">
                               Pipeline Execution Failed
                            </span>
                          </div>
                          <h1 style="margin: 0 0 6px 0; color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">
                            AIC News System Error
                          </h1>
                        </td>
                      </tr>

                      <!-- Body Content Area -->
                      <tr>
                        <td style="padding: 30px;">
                          <p style="margin: 0 0 16px 0; font-size: 15px; color: #334155; font-weight: 500;">
                            Diagnostic Alert,
                          </p>
                          <p style="margin: 0 0 22px 0; font-size: 14px; color: #475569; line-height: 1.65;">
                            The autonomous news system encountered an unhandled exception during the scheduled weekly run. The process has been halted, and no digests were dispatched to the R&D Team.
                          </p>

                          <!-- Error Trace Box (Red Accent) -->
                          <div style="background-color: #fff1f2; padding: 16px 20px; border-radius: 0 10px 10px 0; margin-bottom: 24px; border: 1px solid #ffe4e6; border-left: 4px solid #e11d48;">
                            <p style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; color: #9f1239; text-transform: uppercase; letter-spacing: 0.8px;">
                              System Exception Output:
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #4c0519; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; word-break: break-word;">
                              {error_details}
                            </p>
                          </div>

                          <p style="margin: 0; font-size: 13px; color: #64748b; line-height: 1.6;">
                            <strong>Recommended Action:</strong> Check the Cloud Run job execution logs in GCP for the full stack trace, or review the recent runs in LangSmith to isolate which specific agent node failed.
                          </p>
                        </td>
                      </tr>

                      <!-- Footer -->
                      <tr>
                        <td style="background-color: #f8fafc; padding: 14px 30px; text-align: center; border-top: 1px solid #f1f5f9;">
                          <p style="margin: 0; font-size: 11px; color: #94a3b8; letter-spacing: 0.3px;">
                            © {current_year} APU AI Club (AIC) • Powered By AI Potential • Automated Diagnostic Alert 
                          </p>
                        </td>
                      </tr>

                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """