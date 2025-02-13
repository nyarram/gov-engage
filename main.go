package main

import (
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "Political Engagement API is Running!",
		})
	})

	// Fetch local government details
	r.GET("/local", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"level":          "Local",
			"representative": "John Doe",
			"next_election":  "2026-11-08",
			"promises":       []string{"Better roads", "More schools"},
			"progress":       "50% complete",
		})
	})

	// Fetch state government details
	r.GET("/state", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"level":          "State",
			"representative": "Jane Smith",
			"next_election":  "2026-11-08",
			"promises":       []string{"Healthcare reform", "Green energy"},
			"progress":       "30% complete",
		})
	})

	// Fetch national government details
	r.GET("/national", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"level":          "National",
			"representative": "Alex Johnson",
			"next_election":  "2028-11-08",
			"promises":       []string{"Tax cuts", "Foreign policy improvement"},
			"progress":       "60% complete",
		})
	})

	r.Run(":8080") // Start server on port 8080
}
