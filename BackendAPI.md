# Backend API #

The following abstract methods should be implemented when you write a new cloud backend. The prototypes may be changed later until we reach a stabilized release. We need to clean up and design more abstract common API layer to be compatible with various cloud-computing services.

## Minimum Requirement ##

  * [See Amazon EC2 backend class.](http://code.google.com/p/cciu-open-course-labs/source/browse/opencourselabs/cloud/backends/amazon-ec2.py)
  * This class does not implement Hadoop Cluster APIs which are specific to NexR iCube. But it is _possible_ to implement it. Live patches are welcome!

## Details ##

  * [See the abstract base class.](http://code.google.com/p/cciu-open-course-labs/source/browse/opencourselabs/cloud/backends/__init__.py)

## API Documentation ##
  * [Amazon EC2 Query API](http://docs.amazonwebservices.com/AWSEC2/latest/APIReference/)
  * NexR iCube REST API (will be available soon)