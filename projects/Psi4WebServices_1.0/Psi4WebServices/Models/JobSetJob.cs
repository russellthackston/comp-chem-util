using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace Psi4WebServices.Models
{
    public class JobSetJob : Job
    {
        public JobSetJob(int id, string name, string inputFile, DateTime created, int jobSetJobID) : base(id, name, inputFile, created)
        {
            JobSetJobID = jobSetJobID;
        }
        public int JobSetJobID { get; set; }
    }
}