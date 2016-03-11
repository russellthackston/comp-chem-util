using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace Psi4WebServices.Models
{
    public class JobSet
    {
        public JobSet(string name, DateTime created)
        {
            Name = name;
            Created = created;
        }
        public JobSet(int id, string name, DateTime created)
        {
            ID = id;
            Name = name;
            Created = created;
        }
        public int ID { get; set; }
        public string Name { get; set; }
        public DateTime Created { get; set; }
    }
}