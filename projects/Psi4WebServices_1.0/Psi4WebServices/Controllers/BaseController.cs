using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

using System.Text;
using System.Net.Http.Headers;
using Psi4WebServices.Controllers.Data;

namespace Psi4WebServices.Controllers
{
    public class BaseController : ApiController
    {

        private HttpRequestHeaders headers = null;

        protected string requiredAuth = "Blocked";
        
        protected static string GetParameter(HttpRequestMessage msg, string key)
        {
            string value = null;
            IEnumerable<KeyValuePair<string, string>> list = msg.GetQueryNameValuePairs();
            foreach (KeyValuePair<string, string> item in list)
            {
                if (item.Key.ToLower() == key.ToLower())
                {
                    value = item.Value;
                    break;
                }
            }
            return value;
        }

        protected void CheckAuth()
        {
            string securityToken = null;
            var re = Request;
            if (headers == null)
            {
                headers = (HttpRequestHeaders)re.Headers;
            }
            if (headers.Contains("Authorization"))
            {
                securityToken = headers.GetValues("Authorization").First();
            }

            if (requiredAuth == "None")
            {
                return;
            } else if (securityToken == null || securityToken.Trim() == "") {
                HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.BadRequest);
                response.ReasonPhrase = "Bad auth token";
                response.Content = new StringContent("Bad auth token");
                throw new HttpResponseException(response);
            }

            AuthDataAccess db = new AuthDataAccess();
            if (!db.IsAuthorized(securityToken, requiredAuth))
            {
                HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.BadRequest);
                response.ReasonPhrase = "Bad auth token";
                response.Content = new StringContent("Bad auth token");
                throw new HttpResponseException(response);
            }
        }

        public string RequiredAuthorizationLevel
        {
            get { return this.requiredAuth; }
            set { this.requiredAuth = value; }
        }

        public HttpRequestHeaders Headers
        {
            get { return this.headers; }
            set { this.headers = value; }
        }
    }
}
