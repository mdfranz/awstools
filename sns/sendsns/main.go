package main


/*

Originally based on https://gocodecloud.com/blog/2016/02/20/aws-in-go-part-1---sns/

*/ 


import (
	"io/ioutil"
	"os"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sns"
)

func main() {
	var topic string = os.Getenv("SNS_TOPIC_ARN")
	var data []byte
	var err error

	data, err = ioutil.ReadAll(os.Stdin)

	if err != nil {                 
		fmt.Println(err.Error())
		return
	}


	svc := sns.New(session.New())

	params := &sns.PublishInput{
		Message: aws.String(string(data)), 
		TopicArn: aws.String(topic),
	}

	resp, err := svc.Publish(params) 

	if err != nil {                 
		fmt.Println(resp)
		fmt.Println(err.Error())

		return
	}
}
